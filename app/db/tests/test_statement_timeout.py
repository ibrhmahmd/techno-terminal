"""Statement timeout is set per transaction (#191): the Supabase transaction
pooler drops libpq startup options, so the engine runs SET LOCAL on begin."""
import pytest
from sqlalchemy import exc, text

from app.db.connection import get_session


def _timeout(session) -> str:
    return session.execute(text("SHOW statement_timeout")).scalar_one()


def test_every_transaction_gets_the_60s_timeout():
    with get_session() as session:
        assert _timeout(session) == "1min"


def test_a_cancelled_query_does_not_leak_a_lowered_timeout():
    with get_session() as session:
        session.execute(text("SET LOCAL statement_timeout = '100ms'"))
        with pytest.raises(exc.OperationalError, match="statement timeout"):
            session.execute(text("SELECT pg_sleep(1)"))
        session.rollback()
        assert _timeout(session) == "1min"


def test_listener_overrides_the_connection_default():
    """Like the pooler, drop the startup option's effect: the begin listener still sets 1min."""
    from app.db.connection import get_engine

    with get_engine().connect() as conn:
        conn.exec_driver_sql("SET SESSION statement_timeout = '5s'")
        conn.commit()
        try:
            with conn.begin():
                assert conn.exec_driver_sql("SHOW statement_timeout").scalar_one() == "1min"
        finally:
            conn.exec_driver_sql("RESET statement_timeout")
            conn.commit()
