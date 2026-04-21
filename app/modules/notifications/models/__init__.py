"""
app/modules/notifications/models/__init__.py
─────────────────────────────────────────────
Notification domain models.
"""

from .notification_template import NotificationTemplate
from .notification_log import NotificationLog

__all__ = [
    "NotificationTemplate",
    "NotificationLog",
]
