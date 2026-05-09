import threading
from contextlib import contextmanager
from sqlmodel import create_engine, Session

from app.core.config import settings

_engine = None
_engine_lock = threading.Lock()


def get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = create_engine(
                    settings.database_url,
                    pool_size=5,
                    max_overflow=5,
                    pool_timeout=30,
                    pool_pre_ping=True,
                    pool_recycle=240,
                    connect_args={
                        "keepalives": 1,
                        "keepalives_idle": 30,
                        "keepalives_interval": 10,
                        "keepalives_count": 5,
                        "sslmode": "require",
                        "options": "-c statement_timeout=30000",
                    },
                )
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
