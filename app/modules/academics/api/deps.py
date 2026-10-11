"""Academics HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.dependencies import UoW
from app.modules.academics.services.course_service import CourseService
from app.modules.academics.services.group_service import GroupCoreService
from app.modules.academics.services.group_directory_service import GroupDirectoryService
from app.modules.academics.services.group_level_service import GroupLevelService
from app.modules.academics.services.session_service import SessionService
from app.modules.academics.services.group_analytics_service import GroupAnalyticsService


def get_course_service(
    uow: UoW,
) -> CourseService:
    """Returns a CourseService with request-scoped UnitOfWork."""
    return CourseService(uow)


def get_group_service(
    uow: UoW,
) -> GroupCoreService:
    """Returns a fresh GroupCoreService instance per request."""
    return GroupCoreService(uow)


def get_group_directory_service(
    uow: UoW,
) -> GroupDirectoryService:
    """Returns a GroupDirectoryService with request-scoped UnitOfWork."""
    return GroupDirectoryService(uow)


def get_group_level_service(
    uow: UoW,
) -> GroupLevelService:
    """Returns a GroupLevelService with request-scoped UnitOfWork."""
    return GroupLevelService(uow)


def get_session_service(
    uow: UoW,
) -> SessionService:
    """Returns a SessionService with request-scoped UnitOfWork."""
    return SessionService(uow)


def get_group_analytics_service(
    uow: UoW,
) -> GroupAnalyticsService:
    """Returns a GroupAnalyticsService with request-scoped UnitOfWork."""
    return GroupAnalyticsService(uow)