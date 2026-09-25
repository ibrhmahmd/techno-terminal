"""
app/modules/notifications/interfaces/__init__.py
─────────────────────────────────────────────────
Abstract interfaces for the Notification module.
"""
from app.modules.notifications.interfaces.i_notification_repository import (
    NotificationRepositoryInterface,
)
from app.modules.notifications.interfaces.i_report_delivery_ledger import (
    ReportDeliveryLedgerInterface,
)

__all__ = ["NotificationRepositoryInterface", "ReportDeliveryLedgerInterface"]
