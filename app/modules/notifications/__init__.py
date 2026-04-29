"""
app/modules/notifications/__init__.py
─────────────────────────────────────
Notification module — WhatsApp & Email dispatch with template rendering.
"""

from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.models.notification_log import NotificationLog

__all__ = [
    "NotificationTemplate",
    "NotificationLog",
]
