"""
app/modules/notifications/constants.py
──────────────────────────────────────
Value sets for notification fields (#141). Channel, status and recipient type
mirror the CHECK constraints on notification_templates / notification_logs.
"""
from typing import Literal, TypeAlias

NotificationChannel: TypeAlias = Literal["EMAIL", "WHATSAPP"]
NotificationStatus: TypeAlias = Literal["PENDING", "SENT", "FAILED"]
RecipientType: TypeAlias = Literal["PARENT", "EMPLOYEE", "ADDITIONAL"]

# Columns GET /notifications/logs may sort by.
LogSortField: TypeAlias = Literal[
    "id", "created_at", "sent_at", "status", "channel",
    "recipient_type", "recipient_contact", "subject", "template_id",
]
SortOrder: TypeAlias = Literal["asc", "desc"]

# Every type the services pass to _resolve_notification_recipients; the admin
# settings only mean something for these (kept in step by a test).
NotificationType: TypeAlias = Literal[
    "absence_alert",
    "admin_login_alert",
    "bulk",
    "competition_fee_payment",
    "competition_placement",
    "competition_team_registration",
    "daily_report",
    "enrollment_created",
    "enrollment_dropped",
    "enrollment_transferred",
    "enrollment_updated",
    "monthly_report",
    "payment_received",
    "task_status_changed",
    "weekly_report",
]
