from typing import Optional
from sqlmodel import Session

from app.core.database import get_session
from app.modules.crm.repositories.student_repository import StudentRepository
from app.modules.crm.repositories.parent_repository import ParentRepository

class StudentUnitOfWork:
    """
    Unit of Work for student operations.
    Manages a single DB session across StudentRepository and ParentRepository.
    Ensures atomic commits/rollbacks.

    Usage:
        with StudentUnitOfWork() as uow:
            student = uow.students.create(student_obj)
            uow.parents.create(parent_obj)
            uow.commit()
    """
    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._own_session = session is None
        self._students: Optional[StudentRepository] = None
        self._parents: Optional[ParentRepository] = None

    def __enter__(self) -> "StudentUnitOfWork":
        if self._own_session:
            self._session_cm = get_session()
            self._session = self._session_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        if self._own_session:
            self._session_cm.__exit__(exc_type, exc_val, exc_tb)

    @property
    def students(self) -> StudentRepository:
        if self._students is None:
            self._students = StudentRepository(self._session)
        return self._students

    @property
    def parents(self) -> ParentRepository:
        if self._parents is None:
            self._parents = ParentRepository(self._session)
        return self._parents

    def commit(self) -> None:
        self._session.commit()
        
    def rollback(self) -> None:
        self._session.rollback()
        
    def flush(self) -> None:
        self._session.flush()
