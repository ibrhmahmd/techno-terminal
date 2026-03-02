import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

load_dotenv()

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.environ["DATABASE_URL"]
        _engine = create_engine(
            url,
            pool_size=5,
            max_overflow=5,
            pool_timeout=30,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
    return _engine


@contextmanager
def get_session():
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
