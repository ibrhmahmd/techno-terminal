"""CRM HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.dependencies import UoW
from app.modules.crm.services import (
    StudentCrudService,
    ParentCrudService,
    SearchService,
    StudentProfileService,
    StudentActivityService,
)


def get_student_crud_service(
    uow: UoW,
) -> StudentCrudService:
    """Returns a StudentCrudService with request-scoped UnitOfWork and activity logging."""
    activity_svc = StudentActivityService(uow)
    return StudentCrudService(uow, activity_svc=activity_svc)


def get_student_search_service(
    uow: UoW,
) -> SearchService:
    """Returns a SearchService with request-scoped UnitOfWork."""
    return SearchService(uow)


def get_student_profile_service(
    uow: UoW,
) -> StudentProfileService:
    """Returns a StudentProfileService with request-scoped UnitOfWork."""
    return StudentProfileService(uow)


def get_student_activity_service(
    uow: UoW,
) -> StudentActivityService:
    """Returns a StudentActivityService with request-scoped UnitOfWork."""
    return StudentActivityService(uow)


def get_parent_crud_service(
    uow: UoW,
) -> ParentCrudService:
    """Returns a ParentCrudService with request-scoped UnitOfWork."""
    return ParentCrudService(uow)