"""
app/db/query_logger.py
──────────────────────
DEBUG-level logging of every SQL query with duration and optional request ID.

Install on an engine via:
    install_query_logger(engine)

Uses contextvars to propagate the current request ID from the logging middleware
so every query log line can be correlated with the HTTP request that triggered it.
"""
import contextvars
import logging
import time

from sqlalchemy import Engine, event

logger = logging.getLogger("api.db")

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "db_request_id", default=""
)


def set_db_request_id(request_id: str) -> None:
    """Store the current request ID for DB query log correlation."""
    request_id_var.set(request_id)


@event.listens_for(Engine, "before_cursor_execute")
def _before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    conn._query_start_time = time.perf_counter()


@event.listens_for(Engine, "after_cursor_execute")
def _after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    total = round((time.perf_counter() - conn._query_start_time) * 1000, 1)
    rid = request_id_var.get()
    # Truncate very long statements to keep log lines readable
    stmt = statement if len(statement) <= 500 else statement[:500] + "..."
    logger.debug(
        "[%s] %dms — %s",
        rid or "-",
        total,
        stmt.replace("\n", " ").strip(),
    )


def install_query_logger(engine: Engine) -> None:
    """Attach query logging listeners to *engine*.

    Safe to call multiple times — subsequent calls are idempotent
    (SQLAlchemy ignores duplicate event listeners).
    """
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)
