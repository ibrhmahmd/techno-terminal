"""Tests for the UnitOfWork primitive and its HTTP dependency."""
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.dependencies import UoW
from app.api.exceptions import register_exception_handlers
from app.db.connection import get_engine, get_session
from app.db.uow import unit_of_work


@pytest.fixture
def scratch_table():
    """A dedicated scratch table with a deferred unique constraint.

    Dropped on teardown so the test leaves nothing behind.
    """
    engine = get_engine()
    name = f"uow_scratch_{uuid.uuid4().hex[:12]}"
    with engine.begin() as conn:
        conn.exec_driver_sql(
            f"CREATE TABLE {name} ("
            "id SERIAL PRIMARY KEY, "
            "label TEXT NOT NULL, "
            f"CONSTRAINT {name}_uq UNIQUE (label) DEFERRABLE INITIALLY DEFERRED)"
        )
    try:
        yield name
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql(f"DROP TABLE IF EXISTS {name}")


def _labels(name: str) -> list[str]:
    with get_session() as session:
        rows = session.exec(text(f"SELECT label FROM {name}")).all()
    return [row[0] for row in rows]


def test_committed_work_persists(scratch_table):
    with unit_of_work() as uow:
        uow.session.execute(
            text(f"INSERT INTO {scratch_table} (label) VALUES ('persisted')")
        )
        uow.commit()

    assert _labels(scratch_table) == ["persisted"]


def test_exception_rolls_back_and_reraises(scratch_table):
    with pytest.raises(RuntimeError, match="boom"):
        with unit_of_work() as uow:
            uow.session.execute(
                text(f"INSERT INTO {scratch_table} (label) VALUES ('discarded')")
            )
            raise RuntimeError("boom")

    assert _labels(scratch_table) == []


def test_exit_without_commit_discards(scratch_table):
    with unit_of_work() as uow:
        uow.session.execute(
            text(f"INSERT INTO {scratch_table} (label) VALUES ('uncommitted')")
        )

    assert _labels(scratch_table) == []


def test_http_failed_commit_returns_error_envelope(scratch_table):
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/write")
    def write(uow: UoW):
        uow.session.execute(
            text(f"INSERT INTO {scratch_table} (label) VALUES ('dup')")
        )
        uow.session.execute(
            text(f"INSERT INTO {scratch_table} (label) VALUES ('dup')")
        )
        uow.commit()
        return {"success": True}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/write")

    assert response.status_code != 200
    assert response.status_code >= 500
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "InternalServerError"
