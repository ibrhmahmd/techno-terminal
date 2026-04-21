# app/modules/notifications/services/__init__.py
"""
Notification service exports.
Refactored into focused modules by domain:
- enrollment_notifications: Enrollment lifecycle
- payment_notifications: Payment events
- report_notifications: Scheduled reports
- base_notification_service: Shared helpers
- notification_service: Thin orchestrator (backward compatible)
"""

from .base_notification_service import BaseNotificationService
from .enrollment_notifications import EnrollmentNotificationService
from .payment_notifications import PaymentNotificationService
from .report_notifications import ReportNotificationService
from .notification_service import NotificationService

__all__ = [
    "BaseNotificationService",
    "EnrollmentNotificationService",
    "PaymentNotificationService",
    "ReportNotificationService",
    "NotificationService",
]
