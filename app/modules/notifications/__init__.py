"""
app/modules/notifications/__init__.py
─────────────────────────────────────
Notification module — WhatsApp & Email dispatch with template rendering.
"""

from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.models.notification_log import NotificationLog
from app.modules.notifications.models.notification_subscriber import NotificationSubscriber

__all__ = [
    "NotificationTemplate",
    "NotificationLog",
    "NotificationSubscriber",
]
