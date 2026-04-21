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
        Filters by admin settings - only returns admins who have this notification enabled.
        Also includes additional recipients (non-admins).
        recipient_type: 'ADMIN' or 'ADDITIONAL'
        """
        from app.modules.auth.models.auth_models import User
        
        recipients = []
        
        # 1. Get admins who have this notification enabled
        # Check if admin_notification_settings table exists and has settings
        try:
            stmt = f"""
                SELECT u.id, u.email 
                FROM users u
                LEFT JOIN admin_notification_settings ans ON u.id = ans.admin_id 
                    AND ans.notification_type = '{notification_type}'
                WHERE u.role = 'admin'
                AND (ans.is_enabled IS NULL OR ans.is_enabled = true)
            """
            result = self._repo._session.exec(stmt).all()
            for admin_id, email in result:
                if email:
                    recipients.append((email, admin_id, "ADMIN"))
        except Exception:
            # Fallback: if table doesn't exist or error, return all admins
            stmt = select(User).where(User.role == "admin")
            admins = self._repo._session.exec(stmt).all()
            for admin in admins:
                if admin.email:
                    recipients.append((admin.email, admin.id, "ADMIN"))
        
        # 2. Get additional recipients for enabled admins
        # For each admin that has this notification enabled, get their additional recipients
        try:
            for admin_email, admin_id, _ in recipients:
                stmt_additional = f"""
                    SELECT email
                    FROM notification_additional_recipients
                    WHERE admin_id = {admin_id}
                    AND is_active = true
                    AND (notification_types IS NULL OR '{notification_type}' = ANY(notification_types))
                """
                additional = self._repo._session.exec(stmt_additional).all()
                for (email,) in additional:
                    if email and email not in [r[0] for r in recipients]:
                        recipients.append((email, admin_id, "ADDITIONAL"))
        except Exception:
            # Ignore errors if table doesn't exist
            pass
        
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
