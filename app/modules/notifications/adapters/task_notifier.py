"""Adapter implementing TaskNotifier using NotificationService (ADR-0007)."""

import uuid
from typing import Optional

from fastapi import BackgroundTasks, Depends

from app.modules.notifications.api.deps import get_notification_service
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.tasks import TaskNotifier


class NotificationServiceTaskNotifier:
    """Adapts NotificationService to the TaskNotifier port."""

    def __init__(self, background_tasks: BackgroundTasks, notif_svc: NotificationService):
        self._background_tasks = background_tasks
        self._notif_svc = notif_svc

    def task_assigned(
        self, *, task_id: uuid.UUID, employee_id: int, assigned_by_user_id: Optional[int]
    ) -> None:
        self._notif_svc.task.notify_task_assigned(
            task_id=str(task_id),
            employee_id=employee_id,
            assigned_by_user_id=assigned_by_user_id,
            background_tasks=self._background_tasks,
        )

    def task_status_changed(
        self,
        *,
        task_id: uuid.UUID,
        employee_id: Optional[int],
        old_status: str,
        new_status: str,
        changed_by_user_id: Optional[int],
    ) -> None:
        self._notif_svc.task.notify_task_status_changed(
            task_id=str(task_id),
            employee_id=employee_id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
            background_tasks=self._background_tasks,
        )

    def task_comment_added(
        self, *, task_id: uuid.UUID, comment_id: uuid.UUID, author_user_id: int
    ) -> None:
        self._notif_svc.task.notify_task_comment_added(
            task_id=str(task_id),
            comment_id=str(comment_id),
            author_user_id=author_user_id,
            background_tasks=self._background_tasks,
        )


def get_task_notifier(
    background_tasks: BackgroundTasks,
    notif_svc: NotificationService = Depends(get_notification_service),
) -> TaskNotifier:
    """FastAPI dependency factory for the TaskNotifier adapter."""
    return NotificationServiceTaskNotifier(background_tasks=background_tasks, notif_svc=notif_svc)
