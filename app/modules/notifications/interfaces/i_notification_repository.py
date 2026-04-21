"""
app/modules/notifications/interfaces/i_notification_repository.py
─────────────────────────────────────────────────────────────────
Protocol interface for the notification repository.
"""
from typing import Protocol, Optional, List

from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.models.notification_log import NotificationLog


class INotificationRepository(Protocol):
    """Data-access contract for the notification domain."""

    # ── Templates ────────────────────────────────────────────────────────────
    def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]: ...
    def get_template_by_code(self, code: str) -> Optional[NotificationTemplate]: ...
    def get_template_by_id(self, template_id: int) -> Optional[NotificationTemplate]: ...
    def get_all_templates(self) -> List[NotificationTemplate]: ...
    def create_template(
        self, name: str, channel: str, body: str, variables: List[str],
        subject: Optional[str] = None, is_standard: bool = False,
    ) -> NotificationTemplate: ...
    def update_template(
        self, template_id: int, **kwargs
    ) -> Optional[NotificationTemplate]: ...
    def delete_template(self, template_id: int) -> bool: ...

    # ── Logs ─────────────────────────────────────────────────────────────────
    def create_log(
        self, template_id: Optional[int], channel: str,
        recipient_type: str, recipient_id: int, recipient_contact: str,
        body: str, subject: Optional[str] = None,
    ) -> NotificationLog: ...
    def update_log_status(
        self, log_id: int, status: str, error_message: Optional[str] = None,
    ) -> None: ...
    def get_logs(
        self, recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
        limit: int = 50, offset: int = 0,
    ) -> List[NotificationLog]: ...
    def count_logs(
        self, recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
    ) -> int: ...

