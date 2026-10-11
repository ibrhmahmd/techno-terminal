"""Notification template CRUD and template test-send."""
from typing import Optional

from app.db.uow import unit_of_work
from app.modules.notifications.interfaces.i_notification_repository import (
    NotificationRepositoryInterface,
)
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.repositories.admin_settings_repository import AdminSettingsRepository
from app.modules.notifications.schemas.template_dto import TemplateTestResultDTO
from app.modules.notifications.services.report_notifications import ReportNotificationService


class TemplateService:
    def __init__(self, repo: NotificationRepositoryInterface) -> None:
        self._repo = repo
        self._reports = ReportNotificationService(repo)

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

    async def test_and_send_template(self, template_id: int) -> "TemplateTestResultDTO":
        """
        Test a template by rendering with placeholders and ACTUALLY sending test emails.
        
        Returns TemplateTestResultDTO with rendered content and actual send results.
        """
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
        with unit_of_work() as uow:
            recipients_data = AdminSettingsRepository(uow.session).get_additional_recipients()
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
                await self._reports.dispatch_notification(
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
