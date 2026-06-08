"""
app/modules/notifications/interfaces/__init__.py
─────────────────────────────────────────────────
Abstract interfaces for the Notification module.
"""
from app.modules.notifications.interfaces.i_notification_repository import (
    NotificationRepositoryInterface,
)

__all__ = ["NotificationRepositoryInterface"]
