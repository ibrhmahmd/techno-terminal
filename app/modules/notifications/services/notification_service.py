"""
app/modules/notifications/services/notification_service.py
──────────────────────────────────────────────────────────
Main notification orchestrator - delegates to specialized services.

Refactored to split 777-line monolith into focused modules:
- base_notification_service.py (shared helpers)
- enrollment_notifications.py (enrollment lifecycle)
- payment_notifications.py (payment events)
- report_notifications.py (scheduled reports)
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import BackgroundTasks

from app.modules.notifications.interfaces.i_notification_repository import INotificationRepository
from app.modules.notifications.services.enrollment_notifications import EnrollmentNotificationService
from app.modules.notifications.services.payment_notifications import PaymentNotificationService
from app.modules.notifications.services.report_notifications import ReportNotificationService
from app.modules.notifications.services.competition_notifications import CompetitionNotificationService
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.schemas.template_dto import TemplateTestResultDTO
from app.db.connection import get_session
from app.modules.notifications.repositories.admin_settings_repository import AdminSettingsRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main notification orchestrator - thin facade over specialized services.
    
    Usage:
        service = NotificationService(repo)
        service.enrollment.notify_enrollment_created(...)
        service.payment.notify_payment_received(...)
        service.competition.notify_team_registration(...)
        await service.report.send_daily_report()
    """

    def __init__(self, repo: INotificationRepository):
        self._repo = repo
        # Delegate to specialized services
        self.enrollment = EnrollmentNotificationService(repo)
        self.payment = PaymentNotificationService(repo)
        self.report = ReportNotificationService(repo)
        self.competition = CompetitionNotificationService(repo)


    # ── Template CRUD (delegates to self._repo) ─────────────────────────

    def get_all_templates(self) -> list[NotificationTemplate]:
        return self._repo.get_all_templates()

    def get_template_by_id(self, template_id: int) -> Optional[NotificationTemplate]:
        return self._repo.get_template_by_id(template_id)

    def create_template(self, **data) -> NotificationTemplate:
        return self._repo.create_template(**data)

    def update_template(self, template_id: int, **data) -> Optional[NotificationTemplate]:
        return self._repo.update_template(template_id, **data)

    def delete_template(self, template_id: int) -> bool:
        return self._repo.delete_template(template_id)

    def get_logs(
        self,
        recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        return self._repo.get_logs(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            limit=limit,
            offset=offset,
        )

    def close_session(self) -> None:
        self._repo._session.close()

    # ── Scheduled Reports (delegate to self.report) ─────────────────────

    async def send_daily_report(self) -> None:
        """Daily business summary to DAILY subscribers."""
        await self.report.send_daily_report()

    async def send_weekly_report(self) -> None:
        """Weekly business summary to WEEKLY subscribers."""
        await self.report.send_weekly_report()

    async def send_monthly_report(self) -> None:
        """Monthly business summary to MONTHLY subscribers."""
        await self.report.send_monthly_report()

    # ── Bulk Marketing (kept here for now - simple delegation) ────────────
    # TODO: Move to BulkNotificationService if needed

    def send_bulk(
        self,
        parent_ids: list[int],
        template_name: str,
        extra_vars: dict,
        background_tasks: BackgroundTasks,
    ) -> int:
        """Queues WhatsApp messages to a list of parents. Returns queued count."""
        # Simple implementation - delegates to report service's bulk handling
        return self.report.send_bulk(parent_ids, template_name, extra_vars, background_tasks)

    # ── Template Testing ──────────────────────────────────────────────────

    def test_template(self, template_id: int) -> "TemplateTestResultDTO":
        """
        Test a template by rendering with placeholders and returning send preview.
        
        Returns TemplateTestResultDTO with rendered content and recipient count.
        
        DEPRECATED: Use test_and_send_template() for actual email sending.
        """
        from app.modules.notifications.schemas.template_dto import TemplateTestResultDTO
        from app.db.connection import get_session
        from app.modules.notifications.repositories.admin_settings_repository import AdminSettingsRepository

        # Load template
        template = self._repo.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Generate placeholder values
        placeholders = self._generate_placeholders(template.variables or [])

        # Render template
        rendered_subject = self._render_template(template.subject or "", placeholders)
        rendered_body = self._render_template(template.body, placeholders)

        # Add [TEST] prefix to subject
        rendered_subject = f"[TEST] {rendered_subject}" if rendered_subject else "[TEST] Notification"

        # Get all additional recipients
        with get_session() as session:
            repo = AdminSettingsRepository(session)
            recipients = repo.get_additional_recipients()
            active_recipients = [r for r in recipients if r.get("is_active") and r.get("email")]

        # Count recipients (email sending is stubbed for now)
        sent_count = len(active_recipients)
        failed_count = 0
        errors = []

        return TemplateTestResultDTO(
            template_id=template.id,
            template_name=template.name,
            rendered_subject=rendered_subject,
            rendered_body=rendered_body,
            recipients_sent=sent_count,
            recipients_failed=failed_count,
            errors=errors,
        )
    
    async def test_and_send_template(self, template_id: int) -> "TemplateTestResultDTO":
        """
        Test a template by rendering with placeholders and ACTUALLY sending test emails.
        
        Returns TemplateTestResultDTO with rendered content and actual send results.
        """
        from app.modules.notifications.schemas.template_dto import TemplateTestResultDTO
        from app.db.connection import get_session
        from app.modules.notifications.repositories.admin_settings_repository import AdminSettingsRepository
        from app.modules.notifications.models.notification_template import NotificationTemplate

        # Load template
        template = self._repo.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Generate placeholder values
        placeholders = self._generate_placeholders(template.variables or [])

        # Render template
        rendered_subject = self._render_template(template.subject or "", placeholders)
        rendered_body = self._render_template(template.body, placeholders)

        # Add [TEST] prefix to subject
        rendered_subject = f"[TEST] {rendered_subject}" if rendered_subject else "[TEST] Notification"

        # Get all additional recipients
        with get_session() as session:
            repo = AdminSettingsRepository(session)
            recipients_data = repo.get_additional_recipients()
            active_recipients = [r for r in recipients_data if r.get("is_active") and r.get("email")]

        # Actually send test emails to all active recipients
        sent_count = 0
        failed_count = 0
        errors = []
        
        # Create a notification template for sending
        test_template = NotificationTemplate(
            id=template.id,
            name=template.name,
            body=rendered_body,
            subject=rendered_subject,
            channel="EMAIL",
            is_active=True
        )
        
        # Send to each recipient using report service's dispatch
        for recipient in active_recipients:
            email = recipient.get("email")
            recipient_id = recipient.get("id", 0)
            
            if not email:
                failed_count += 1
                errors.append(f"Missing email for recipient {recipient_id}")
                continue
                
            try:
                # Send test email using report service's dispatch
                await self.report.dispatch_notification(
                    template=test_template,
                    channel="EMAIL",
                    recipient_type="ADDITIONAL",
                    recipient_id=recipient_id,
                    contact=email,
                    variables=placeholders
                )
                sent_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to send to {email}: {str(e)}")

        return TemplateTestResultDTO(
            template_id=template.id,
            template_name=template.name,
            rendered_subject=rendered_subject,
            rendered_body=rendered_body,
            recipients_sent=sent_count,
            recipients_failed=failed_count,
            errors=errors,
        )

    def _generate_placeholders(self, variables: list[str]) -> dict[str, str]: 
        """Generate human-readable placeholder values for template variables."""
        placeholders = {}
        for var in variables:
            # Convert snake_case to Title Case: parent_name -> [Parent Name]
            human_readable = var.replace("_", " ").title()
            placeholders[var] = f"[{human_readable}]"
        return placeholders

    def _render_template(self, template_str: str, variables: dict[str, str]) -> str:
        """Render template string with variable placeholders using Jinja2-style syntax."""
        result = template_str
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)
        return result
