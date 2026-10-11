"""Adapter implementing EnrollmentNotifier using the notification services (ADR-0007)."""

from typing import Optional

from fastapi import BackgroundTasks, Depends

from app.modules.notifications.api.deps import get_enrollment_notification_service
from app.modules.enrollments import EnrollmentNotifier
from app.modules.notifications.services.enrollment_notifications import EnrollmentNotificationService


class NotificationServiceEnrollmentNotifier:
    """Adapts the notification services to the EnrollmentNotifier port."""

    def __init__(self, background_tasks: BackgroundTasks, notif_svc: EnrollmentNotificationService):
        self._background_tasks = background_tasks
        self._notif_svc = notif_svc

    def enrollment_created(
        self, *, student_id: int, enrollment_id: int, group_id: int, level_number: int
    ) -> None:
        self._notif_svc.notify_enrollment_created(
            student_id=student_id,
            enrollment_id=enrollment_id,
            group_id=group_id,
            level_number=level_number,
            background_tasks=self._background_tasks,
        )

    def enrollment_updated(
        self,
        *,
        student_id: int,
        enrollment_id: int,
        group_id: int,
        changes_summary: str,
        performed_by: Optional[int],
    ) -> None:
        self._notif_svc.notify_enrollment_updated(
            student_id=student_id,
            enrollment_id=enrollment_id,
            group_id=group_id,
            changes_summary=changes_summary,
            performed_by=performed_by,
            background_tasks=self._background_tasks,
        )

    def enrollment_transferred(
        self,
        *,
        student_id: int,
        from_enrollment_id: int,
        to_enrollment_id: int,
        from_group_id: int,
        to_group_id: int,
        transferred_by: Optional[int],
    ) -> None:
        self._notif_svc.notify_enrollment_transferred(
            student_id=student_id,
            from_enrollment_id=from_enrollment_id,
            to_enrollment_id=to_enrollment_id,
            from_group_id=from_group_id,
            to_group_id=to_group_id,
            transferred_by=transferred_by,
            background_tasks=self._background_tasks,
        )

    def enrollment_dropped(
        self,
        *,
        student_id: int,
        enrollment_id: int,
        group_id: int,
        reason: Optional[str],
        dropped_by: Optional[int],
    ) -> None:
        self._notif_svc.notify_enrollment_dropped(
            student_id=student_id,
            enrollment_id=enrollment_id,
            group_id=group_id,
            reason=reason,
            dropped_by=dropped_by,
            background_tasks=self._background_tasks,
        )


def get_enrollment_notifier(
    background_tasks: BackgroundTasks,
    notif_svc: EnrollmentNotificationService = Depends(get_enrollment_notification_service),
) -> EnrollmentNotifier:
    """FastAPI dependency factory for the EnrollmentNotifier adapter."""
    return NotificationServiceEnrollmentNotifier(
        background_tasks=background_tasks, notif_svc=notif_svc
    )
