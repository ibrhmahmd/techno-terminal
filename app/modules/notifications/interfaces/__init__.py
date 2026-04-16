"""
app/modules/notifications/interfaces/__init__.py
─────────────────────────────────────────────────
Abstract interfaces for the Notification module.
"""
from app.modules.notifications.interfaces.i_notification_repository import (
    INotificationRepository,
)

__all__ = ["INotificationRepository"]
