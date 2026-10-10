"""Adapter implementing AuthNotifier using NotificationService (ADR-0007)."""

import logging
from fastapi import BackgroundTasks, Depends

from app.api.dependencies import get_notification_service
from app.modules.auth import AuthNotifier
from app.modules.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class NotificationServiceAuthNotifier:
    """Adapts NotificationService to the AuthNotifier port."""

    def __init__(self, background_tasks: BackgroundTasks, notif_svc: NotificationService):
        self._background_tasks = background_tasks
        self._notif_svc = notif_svc

    def admin_login(
        self,
        *,
        username: str,
        email: str,
        role: str,
        ip_address: str,
        user_agent: str,
        alert_reason: str,
    ) -> None:
        self._notif_svc.notify_admin_login(
            username=username,
            email=email,
            role=role,
            ip_address=ip_address,
            user_agent=user_agent,
            alert_reason=alert_reason,
            background_tasks=self._background_tasks,
        )


def get_auth_notifier(
    background_tasks: BackgroundTasks,
    notif_svc: NotificationService = Depends(get_notification_service),
) -> AuthNotifier:
    """FastAPI dependency factory for the AuthNotifier adapter."""
    return NotificationServiceAuthNotifier(background_tasks=background_tasks, notif_svc=notif_svc)