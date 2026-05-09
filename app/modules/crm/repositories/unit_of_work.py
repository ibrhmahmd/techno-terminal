from typing import Optional
from sqlmodel import Session

from app.db.connection import get_session
from app.modules.crm.repositories.student_repository import StudentRepository
from app.modules.crm.repositories.parent_repository import ParentRepository
from app.modules.crm.repositories.activity_repository import ActivityRepository

class StudentUnitOfWork:
    """
    Unit of Work for student operations.
    Manages a single DB session across StudentRepository, ParentRepository, and ActivityRepository.
    Ensures atomic commits/rollbacks with comprehensive activity logging.

    Usage:
        with StudentUnitOfWork() as uow:
            student = uow.students.create(student_obj)
            uow.parents.create(parent_obj)
            uow.activities.log_registration(student.id, performed_by)
            uow.commit()
    """
    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._own_session = session is None
        self._students: Optional[StudentRepository] = None
        self._parents: Optional[ParentRepository] = None
        self._activities: Optional[ActivityRepository] = None

    def __enter__(self) -> "StudentUnitOfWork":
        if self._own_session:
            self._session_cm = get_session()
            self._session = self._session_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._own_session:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
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

    @property
    def activities(self) -> ActivityRepository:
        if self._activities is None:
            self._activities = ActivityRepository(self._session)
        return self._activities

    def commit(self) -> None:
        self._session.commit()
        
    def rollback(self) -> None:
        self._session.rollback()
        
    def flush(self) -> None:
        self._session.flush()
