"""Admin-facing alerts: admin login alert and student absence alert."""
import logging
from datetime import datetime

from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService

logger = logging.getLogger(__name__)


class AlertNotificationService(BaseNotificationService):
    """Handles: admin_login_alert and absence_alert."""

    # ── Auth Alerts ───────────────────────────────────────────────────────

    def notify_admin_login(
        self,
        username: str,
        email: str,
        role: str,
        ip_address: str,
        user_agent: str,
        alert_reason: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Sends an admin_login_alert to all active administrators."""
        template = self._repo.get_template_by_name("admin_login_alert")
        if not template:
            logger.warning("Notification template 'admin_login_alert' not found. Skipping.")
            return

        variables = {
            "username": username,
            "email": email,
            "role": role,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": ip_address or "Unknown",
            "user_agent": user_agent or "Unknown",
            "alert_reason": alert_reason,
        }

        # Resolve admins using base notification service's logic
        recipients = self._resolve_notification_recipients(
            notification_type="admin_login_alert"
        )

        for email_address, recipient_id, recipient_type in recipients:
            background_tasks.add_task(
                self._dispatch,
                template=template,
                channel="EMAIL",
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                contact=email_address,
                variables=variables,
            )

    # ── Absence Alerts ────────────────────────────────────────────────────

    def notify_absence(
        self,
        student_id: int,
        session_name: str,
        session_date: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Send absence alert notification to admins."""
        template = self._repo.get_template_by_name("absence_alert")
        if not template:
            logger.warning("Notification template 'absence_alert' not found. Skipping.")
            return

        student_name = self._get_student_name(student_id)

        variables = {
            "student_name": student_name,
            "session_name": session_name,
            "session_date": session_date,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }

        recipients = self._resolve_notification_recipients(
            notification_type="absence_alert",
            entity_id=student_id,
            entity_description=f"Student #{student_id} - {student_name}",
        )

        for email, recipient_id, recipient_type in recipients:
            background_tasks.add_task(
                self._dispatch,
                template=template,
                channel="EMAIL",
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                contact=email,
                variables=variables,
            )
