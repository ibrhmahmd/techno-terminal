import logging
import re
import threading
from contextlib import contextmanager
from urllib.parse import urlparse

from sqlmodel import create_engine, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

_engine = None
_engine_lock = threading.Lock()

_PROJECT_REF_PATTERN = re.compile(r"^[a-z0-9]{20}$")


def _extract_db_project_ref(database_url: str) -> str | None:
    """Pull the Supabase project ref from a DATABASE_URL, if any."""
    parsed = urlparse(database_url)
    candidates = []
    if parsed.username and "." in parsed.username:
        candidates.append(parsed.username.split(".", 1)[1])
    host_parts = parsed.hostname.split(".") if parsed.hostname else []
    if host_parts:
        candidates.append(host_parts[0])
    for candidate in candidates:
        if _PROJECT_REF_PATTERN.match(candidate):
            return candidate
    return None


def _warn_on_project_mismatch() -> None:
    """Warn when the database and Supabase auth point at different projects.

    This misconfiguration is silent at boot and only surfaces as 403/401s
    or missing local user mappings at request time.
    """
    db_ref = _extract_db_project_ref(settings.database_url)
    auth_ref = None
    try:
        auth_ref = urlparse(settings.supabase_url).hostname.split(".")[0]
    except AttributeError:
        pass
    if (
        db_ref
        and auth_ref
        and _PROJECT_REF_PATTERN.match(auth_ref)
        and db_ref != auth_ref
    ):
        logger.warning(
            "Project mismatch: DATABASE_URL targets '%s' but SUPABASE_URL "
            "targets '%s'. JWT-to-local-user mapping will fail across "
            "projects.",
            db_ref,
            auth_ref,
        )


def get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = create_engine(
                    settings.database_url,
                    pool_size=10,
                    max_overflow=5,
                    pool_timeout=30,
                    pool_pre_ping=True,
                    pool_recycle=240,
                    connect_args={
                        "keepalives": 1,
                        "keepalives_idle": 30,
                        "keepalives_interval": 10,
                        "keepalives_count": 5,
                        "sslmode": "prefer",
                        "options": "-c statement_timeout=30000",
                    },
                )
                _warn_on_project_mismatch()
                from app.db.query_logger import install_query_logger

                install_query_logger(_engine)
    return _engine


@contextmanager
def get_session():
    """
    Yields a session. Caller is responsible for commit.
    Auto-rollback on exception. Auto-close always.
    """
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
