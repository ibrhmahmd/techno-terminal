"""CRM HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends
from sqlmodel import Session

from app.api.dependencies import UoW, get_db
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.services import (
    StudentCrudService,
    ParentCrudService,
    SearchService,
    StudentProfileService,
    StudentActivityService,
)


def get_student_crud_service(
    session: Session = Depends(get_db),
) -> StudentCrudService:
    """Returns a StudentCrudService with a fresh UnitOfWork and activity logging."""
    uow = StudentUnitOfWork(session=session)
    activity_svc = StudentActivityService(uow)
    return StudentCrudService(uow, activity_svc=activity_svc)


def get_student_search_service(
    session: Session = Depends(get_db),
) -> SearchService:
    """Returns a SearchService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return SearchService(uow)


def get_student_profile_service(
    session: Session = Depends(get_db),
) -> StudentProfileService:
    """Returns a StudentProfileService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return StudentProfileService(uow)


def get_student_activity_service(
    session: Session = Depends(get_db),
) -> StudentActivityService:
    """Returns a StudentActivityService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return StudentActivityService(uow)


def get_parent_crud_service(
    session: Session = Depends(get_db),
) -> ParentCrudService:
    """Returns a ParentCrudService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return ParentCrudService(uow)