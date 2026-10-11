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


def get_group_directory_service() -> GroupDirectoryService:
    """Returns a fresh GroupDirectoryService instance per request."""
    return GroupDirectoryService()


def get_group_level_service() -> GroupLevelService:
    """Returns a fresh GroupLevelService instance per request."""
    return GroupLevelService()


def get_session_service(
    uow: UoW,
) -> SessionService:
    """Returns a SessionService with request-scoped UnitOfWork."""
    return SessionService(uow)


def get_group_analytics_service() -> GroupAnalyticsService:
    """Returns a fresh GroupAnalyticsService instance per request."""
    return GroupAnalyticsService()