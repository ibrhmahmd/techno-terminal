"""Adapter implementing AuthNotifier using the notification services (ADR-0007)."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, Depends

from app.modules.notifications.api.deps import get_alert_service
from app.modules.auth import AuthNotifier
from app.modules.notifications.services.alert_notifications import AlertNotificationService

logger = logging.getLogger(__name__)


class NotificationServiceAuthNotifier:
    """Adapts the notification services to the AuthNotifier port."""

    def __init__(self, background_tasks: BackgroundTasks, notif_svc: AlertNotificationService):
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

    def user_invited(
        self,
        *,
        email: str,
        role: str,
        register_url: str,
        expires_at: Optional[datetime],
        employee_id: Optional[int],
    ) -> None:
        self._notif_svc.notify_user_invited(
            email=email,
            role=role,
            register_url=register_url,
            expires_at=expires_at,
            employee_id=employee_id,
            background_tasks=self._background_tasks,
        )


def get_auth_notifier(
    background_tasks: BackgroundTasks,
    notif_svc: AlertNotificationService = Depends(get_alert_service),
) -> AuthNotifier:
    """FastAPI dependency factory for the AuthNotifier adapter."""
    return NotificationServiceAuthNotifier(background_tasks=background_tasks, notif_svc=notif_svc)