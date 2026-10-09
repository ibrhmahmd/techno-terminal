"""Unit of Work — one transaction boundary per use case.

Rule: a use case receives exactly one ``UnitOfWork`` and only the outermost
use case calls ``commit()``. Commit before any external I/O (Supabase, PDF
rendering, email) so a failed commit becomes an error response instead of
work that has already left the process.
"""
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session

from app.db.connection import get_engine


class UnitOfWork:
    """Wraps a single :class:`~sqlmodel.Session` for one use case.

    Services and repositories share the injected instance; only the
    top-level use case calls :meth:`commit`, and it does so before any
    external I/O.
    """

    def __init__(self, session: Session):
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def flush(self) -> None:
        self._session.flush()


@contextmanager
def unit_of_work() -> Iterator[UnitOfWork]:
    """Open a UnitOfWork for non-HTTP entry points.

    Yields a UnitOfWork over a fresh session. On exit any uncommitted work
    is rolled back (and an exception is re-raised); the session is always
    closed. It never auto-commits.
    """
    with Session(get_engine(), expire_on_commit=False) as session:
        uow = UnitOfWork(session)
        try:
            yield uow
        except Exception:
            session.rollback()
            raise
        else:
            session.rollback()
