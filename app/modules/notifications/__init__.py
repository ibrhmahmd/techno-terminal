"""
app/modules/notifications/__init__.py
─────────────────────────────────────
Notifications Module Facade (ADR-0003)

Other modules must import Notifications ONLY via this facade, except
app.modules.notifications.models which anyone may import (ADR-0004).

Exports:
- Models: NotificationTemplate, NotificationLog
- Adapter factories (for create_app() wiring, ADR-0007): get_auth_notifier,
  get_enrollment_notifier, get_competition_notifier, get_payment_notifier,
  get_task_notifier
- Services: ReportNotificationService
- DTOs: ReportDeliveryResult, DailyReportAggregateDTO
"""

from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.models.notification_log import NotificationLog
from app.modules.notifications.schemas.report_dto import (
    DailyReportAggregateDTO,
    ReportDeliveryResult,
)
from app.modules.notifications.services.report_notifications import ReportNotificationService
from app.modules.notifications.adapters import (
    get_auth_notifier,
    get_competition_notifier,
    get_enrollment_notifier,
    get_payment_notifier,
    get_task_notifier,
)

__all__ = [
    "NotificationTemplate",
    "NotificationLog",
    "DailyReportAggregateDTO",
    "ReportDeliveryResult",
    "ReportNotificationService",
    "get_auth_notifier",
    "get_competition_notifier",
    "get_enrollment_notifier",
    "get_payment_notifier",
    "get_task_notifier",
]
