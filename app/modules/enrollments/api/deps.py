"""Enrollments HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends
from sqlmodel import Session

from app.api.dependencies import get_db, get_notification_service
from app.db.uow import UnitOfWork
from app.modules.crm import StudentActivityService
from app.modules.enrollments.core.service import EnrollmentService
from app.modules.enrollments.directory.service import EnrollmentDirectoryService
from app.modules.enrollments.lifecycle.service import EnrollmentLifecycleService


def get_enrollment_service(
    session: Session = Depends(get_db),
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> EnrollmentService:
    """Returns an EnrollmentService with activity logging and notifications."""
    uow = UnitOfWork(session)
    activity_svc = StudentActivityService(uow)
    return EnrollmentService(
        activity_svc=activity_svc,
        notification_svc=notification_svc,
    )


def get_enrollment_directory_service() -> EnrollmentDirectoryService:
    """Returns an EnrollmentDirectoryService for read-only enrollment queries."""
    return EnrollmentDirectoryService()


def get_enrollment_migration_service(
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> EnrollmentLifecycleService:
    """Returns an EnrollmentLifecycleService with notification support."""
    return EnrollmentLifecycleService(notification_svc=notification_svc)


def get_enrollment_lifecycle_service() -> EnrollmentLifecycleService:
    """Dependency provider for the group level progression use case."""
    return EnrollmentLifecycleService()
