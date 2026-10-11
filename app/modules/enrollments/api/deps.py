"""Enrollments HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.deps import UoW
from app.modules.crm import StudentActivityService
from app.modules.enrollments.ports import EnrollmentNotifier
from app.modules.enrollments.services.enrollment_service import EnrollmentService
from app.modules.enrollments.services.enrollment_directory_service import EnrollmentDirectoryService
from app.modules.enrollments.services.enrollment_lifecycle_service import EnrollmentLifecycleService


def get_enrollment_notifier() -> EnrollmentNotifier:
    """EnrollmentNotifier provider — overridden in create_app() with the real adapter."""
    raise NotImplementedError("wired in create_app()")


def get_enrollment_service(
    uow: UoW,
    notifier: EnrollmentNotifier = Depends(get_enrollment_notifier),
) -> EnrollmentService:
    """Returns an EnrollmentService with activity logging and the notifier port."""
    return EnrollmentService(uow, activity_svc=StudentActivityService(uow), notifier=notifier)


def get_enrollment_directory_service(
    uow: UoW,
) -> EnrollmentDirectoryService:
    """Returns an EnrollmentDirectoryService for read-only enrollment queries."""
    return EnrollmentDirectoryService(uow)


def get_enrollment_lifecycle_service(
    uow: UoW,
) -> EnrollmentLifecycleService:
    """Dependency provider for the group level progression use case."""
    return EnrollmentLifecycleService(uow)
