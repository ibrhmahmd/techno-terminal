"""Notification adapters for cross-module ports (ADR-0007)."""

from app.modules.notifications.adapters.auth_notifier import get_auth_notifier
from app.modules.notifications.adapters.enrollment_notifier import get_enrollment_notifier

__all__ = ["get_auth_notifier", "get_enrollment_notifier"]
