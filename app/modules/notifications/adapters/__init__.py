"""Notification adapters for cross-module ports (ADR-0007)."""

from app.modules.notifications.adapters.auth_notifier import get_auth_notifier
from app.modules.notifications.adapters.competition_notifier import get_competition_notifier
from app.modules.notifications.adapters.enrollment_notifier import get_enrollment_notifier
from app.modules.notifications.adapters.payment_notifier import get_payment_notifier
from app.modules.notifications.adapters.task_notifier import get_task_notifier

__all__ = [
    "get_auth_notifier",
    "get_competition_notifier",
    "get_enrollment_notifier",
    "get_payment_notifier",
    "get_task_notifier",
]
