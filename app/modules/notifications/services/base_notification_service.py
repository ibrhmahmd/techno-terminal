"""
app/modules/notifications/services/base_notification_service.py
─────────────────────────────────────────────────────────────
Base helpers for all notification services.
No business logic - just contact resolution, template rendering, dispatch.
"""
import logging
from typing import Optional, Tuple
from sqlmodel import select

from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.dispatchers.whatsapp_dispatcher import TwilioWhatsAppDispatcher
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent
from app.modules.crm.models.student_models import Student


logger = logging.getLogger(__name__)


class BaseNotificationService:
    """Shared infrastructure - no business logic here."""
    
    def __init__(self, repo: NotificationRepository):
        self._repo = repo
        self._email = GmailEmailDispatcher()
        self._whatsapp = TwilioWhatsAppDispatcher()
    
    def _resolve_contact(
        self, student_id: int, channel: str
    ) -> Tuple[Optional[str], Optional[int], str, str]:
        """
        Resolve parent contact for student.
        Returns: (contact, parent_id, parent_name, student_name)
        """
        student = self._repo._session.get(Student, student_id)
        if not student:
            return None, None, "", ""
        
        # Get primary parent
        stmt = select(Parent, StudentParent).join(StudentParent).where(
            StudentParent.student_id == student_id,
            StudentParent.is_primary.is_(True),
        )
        result = self._repo._session.exec(stmt).first()
        
        # Fallback to any parent
        if not result:
            stmt2 = select(Parent, StudentParent).join(StudentParent).where(
                StudentParent.student_id == student_id
            )
            result = self._repo._session.exec(stmt2).first()
        
        if result:
            parent, _ = result
            if channel == "EMAIL":
                contact = parent.email
            else:
                contact = parent.phone_primary
            return contact, parent.id, parent.full_name, student.full_name
        
        return None, None, "", student.full_name
    
    def _resolve_notification_recipients(
        self, notification_type: str
    ) -> list[tuple[str, int, str]]:
        """
        Returns list of (email, recipient_id, recipient_type) tuples.
        Uses only notification_additional_recipients table (global recipients).
        recipient_type: 'ADDITIONAL' (all recipients are treated as additional)
        """
        from sqlalchemy import text

        recipients = []

        # Get all active additional recipients for this notification type (global - no admin_id filter)
        try:
            stmt = text(f"""
                SELECT id, email
                FROM notification_additional_recipients
                WHERE is_active = true
                AND (notification_types IS NULL OR '{notification_type}' = ANY(notification_types))
            """)
            result = self._repo._session.exec(stmt).all()
            for recipient_id, email in result:
                if email:
                    recipients.append((email, recipient_id, "ADDITIONAL"))
        except Exception as e:
            logger.warning(f"Could not fetch additional recipients: {e}")

        return recipients
    
    def _render_template(self, template: NotificationTemplate, variables: dict) -> str:
        """Simple {{key}} substitution."""
        body = template.body
        for key, val in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
        return body
    
    async def _dispatch(
        self, template: NotificationTemplate, channel: str, recipient_type: str,
        recipient_id: int, contact: str, variables: dict
    ) -> None:
        """Send notification and log result."""
        body = self._render_template(template, variables)
        
        subject = None
        if template.subject:
            subject = template.subject
            for key, val in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(val))
        
        # Create log
        log = self._repo.create_log(
            template_id=template.id,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            recipient_contact=contact,
            body=body,
            subject=subject,
        )
        
        # Dispatch (WhatsApp disabled - email only for now)
        success, error = False, "Unknown channel"
        if channel == "WHATSAPP":
            logger.info(f"WhatsApp notifications disabled - skipping message to {recipient_type} {recipient_id}")
            success = True  # Mark as success to avoid retry attempts
        elif channel == "EMAIL":
            success, error = await self._email.send(contact, body, subject)
        
        # Update log
        status = "SENT" if success else "FAILED"
        self._repo.update_log_status(log.id, status, error)
        
        if success:
            logger.info(f"Notification sent to {recipient_type} {recipient_id} via {channel}")
        else:
            logger.error(f"Notification failed to {recipient_type} {recipient_id}: {error}")
