"""Tests for the rollback-only ``uow`` / ``client_with_uow`` fixtures.

Both tests prove that work committed through the fixture (directly via
``uow.session``, or through a route that is injected with the fixture's
``UnitOfWork`` by overriding ``get_uow``) leaves zero rows behind once the
fixture tears down.

Post-teardown guarantee: instead of letting pytest run the fixture teardown
after the test function returns (which would make the assertion impossible in
the same test), each test drives the fixture's own generator manually with
``next()``. Advancing past ``yield`` to ``StopIteration`` executes the
generator's ``finally`` block — exactly the teardown pytest would run — so the
row-presence assertion below it is guaranteed to run after rollback.
"""
import uuid

from fastapi import APIRouter
from sqlalchemy import text

from app.api.dependencies import UoW
from app.db.connection import get_engine
from tests.conftest import app as _app_fixture
from tests.conftest import client_with_uow as _client_with_uow_fixture
from tests.conftest import uow as _uow_fixture


def _scratch_table() -> str:
    """Create a throwaway table on a separate committed connection.

    Returns the table name. The table is dropped by :func:`_drop_scratch_table`.
    Creating it outside any fixture's outer transaction means it is visible to
    every connection, including the one bound to the ``uow`` fixture.
    """
    name = f"uow_fixture_{uuid.uuid4().hex[:12]}"
    with get_engine().begin() as conn:
        conn.exec_driver_sql(
            f"CREATE TABLE {name} (id SERIAL PRIMARY KEY, label TEXT NOT NULL)"
        )
    return name


def _drop_scratch_table(name: str) -> None:
    with get_engine().begin() as conn:
        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {name}")


def _exhaust(generator) -> None:
    """Run a fixture generator's teardown by driving it past ``yield``."""
    try:
        next(generator)
    except StopIteration:
        pass


def _row_count(connection, name: str) -> int:
    return connection.execute(text(f"SELECT count(*) FROM {name}")).scalar_one()


def test_uow_committed_work_rolls_back_at_teardown():
    """Committed work on the ``uow`` fixture disappears after its teardown.

    The fixture's generator is driven manually so the teardown (outer rollback)
    provably happens *before* the "nothing remains" assertion below it.
    """
    name = _scratch_table()
    try:
        uow_generator = _uow_fixture.__wrapped__()
        uow = next(uow_generator)

        uow.session.execute(text(f"INSERT INTO {name} (label) VALUES ('committed')"))
        uow.commit()
        assert uow.session.execute(
            text(f"SELECT count(*) FROM {name}")
        ).scalar_one() == 1

        _exhaust(uow_generator)

        with get_engine().connect() as conn:
            assert _row_count(conn, name) == 0
    finally:
        _drop_scratch_table(name)


def test_route_write_via_client_with_uow_rolls_back_at_teardown():
    """A route served through ``client_with_uow`` leaves zero rows behind.

    A throwaway router is mounted on the real app; its POST handler is injected
    with the fixture's ``UnitOfWork`` via the ``get_uow`` override and commits.
    Teardown is driven manually so both the override pop and the outer rollback
    complete before the "nothing remains" assertion.
    """
    name = _scratch_table()
    try:
        app = _app_fixture.__wrapped__()
        uow_generator = _uow_fixture.__wrapped__()
        uow = next(uow_generator)
        client_generator = _client_with_uow_fixture.__wrapped__(app, uow)
        client = next(client_generator)

        router = APIRouter()

        @router.post("/__test_uow_write")
        def _write_route(u: UoW):
            u.session.execute(text(f"INSERT INTO {name} (label) VALUES ('route')"))
            u.commit()
            return {"success": True}

        routes_before = len(app.router.routes)
        app.include_router(router)

        try:
            response = client.post("/__test_uow_write")
            assert response.status_code == 200, response.text
            assert uow.session.execute(
                text(f"SELECT count(*) FROM {name}")
            ).scalar_one() == 1
        finally:
            del app.router.routes[routes_before:]
            client.close()
            _exhaust(client_generator)
            _exhaust(uow_generator)

        with get_engine().connect() as conn:
            assert _row_count(conn, name) == 0
    finally:
        _drop_scratch_table(name)