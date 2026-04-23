"""
app/modules/notifications/services/base_notification_service.py
─────────────────────────────────────────────────────────────
Base helpers for all notification services.
No business logic - just contact resolution, template rendering, dispatch.
"""
import logging
import os
import re
from datetime import datetime
from typing import Optional, Tuple
from sqlmodel import select

# Fallback email configuration from environment variable
FALLBACK_EMAIL = os.getenv("NOTIFICATION_FALLBACK_EMAIL", "ibrahim.ahmd.net@gmail.com")
FALLBACK_RECIPIENT_ID = -1  # Special ID to indicate fallback

from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.dispatchers.whatsapp_dispatcher import TwilioWhatsAppDispatcher
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.schemas.fallback_dto import FallbackAlertContext
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
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format using regex pattern."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
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
        self,
        notification_type: str,
        entity_id: Optional[int] = None,
        entity_description: Optional[str] = None
    ) -> list[tuple[str, int, str]]:
        """
        Returns list of (email, recipient_id, recipient_type) tuples.
        Uses notification_additional_recipients table with fallback to env-configured email.
        Automatically sends fallback alert if no valid recipients found.
        
        Args:
            notification_type: Type of notification being sent
            entity_id: Optional ID of the entity (receipt, student, etc.) for alert context
            entity_description: Optional human-readable description for alert context
        
        Returns:
            List of (email, recipient_id, recipient_type) tuples
        """
        from sqlalchemy import text

        recipients = []
        invalid_emails_found = []

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
                if email and self._is_valid_email(email):
                    recipients.append((email, recipient_id, "ADDITIONAL"))
                elif email:
                    invalid_emails_found.append((recipient_id, email))
        except Exception as e:
            logger.error(f"Failed to fetch additional recipients: {e}")

        # Check if we need to trigger fallback
        if not recipients:
            # Validate and use fallback email
            if self._is_valid_email(FALLBACK_EMAIL):
                recipients.append((FALLBACK_EMAIL, FALLBACK_RECIPIENT_ID, "FALLBACK"))

                # Log warning
                logger.warning(
                    f"FALLBACK TRIGGERED: No valid recipients for '{notification_type}'. "
                    f"Using fallback email: {FALLBACK_EMAIL}"
                )

                # Create notification log entry for fallback activation
                try:
                    self._repo.create_log(
                        template_id=None,
                        channel="EMAIL",
                        recipient_type="FALLBACK_ALERT",
                        recipient_id=FALLBACK_RECIPIENT_ID,
                        recipient_contact=FALLBACK_EMAIL,
                        body=f"Fallback triggered for notification type: {notification_type}. "
                             f"No valid recipients found in notification_additional_recipients. "
                             f"Invalid emails found: {len(invalid_emails_found)}",
                        subject="Notification Fallback Activated",
                    )
                except Exception as log_error:
                    logger.error(f"Failed to create fallback alert log: {log_error}")

                # Send alert to fallback email with full context
                context = FallbackAlertContext(
                    notification_type=notification_type,
                    entity_id=entity_id,
                    entity_description=entity_description,
                    intended_recipients_count=0
                )
                try:
                    import asyncio
                    asyncio.create_task(self._send_fallback_alert(context))
                except Exception as alert_error:
                    logger.error(f"Failed to send fallback alert: {alert_error}")
            else:
                logger.error(
                    f"CRITICAL: Fallback email '{FALLBACK_EMAIL}' is invalid. "
                    f"Notification '{notification_type}' will not be delivered."
                )

        # Log invalid emails if found
        if invalid_emails_found:
            logger.warning(
                f"Found {len(invalid_emails_found)} invalid email(s) in recipients table: "
                f"{[e for _, e in invalid_emails_found]}"
            )

        return recipients
    
    def _render_template(self, template: NotificationTemplate, variables: dict) -> str:
        """Simple {{key}} substitution."""
        body = template.body
        for key, val in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
        return body
    
    async def _send_fallback_alert(self, context: FallbackAlertContext) -> None:
        """
        Send alert notification to fallback email about fallback activation.
        This is separate from the main notification to alert admins about the issue.
        
        Args:
            context: FallbackAlertContext containing notification details and entity info
        """
        from app.modules.notifications.models.notification_log import NotificationLog
        
        subject = f"[ALERT] Notification Fallback Activated - {context.notification_type}"
        
        # Build entity info section if available
        entity_info = ""
        if context.entity_id:
            entity_info = f"- Entity ID: {context.entity_id}\n"
        if context.entity_description:
            entity_info += f"- Entity Description: {context.entity_description}\n"
        
        body = f"""NOTIFICATION FALLBACK ALERT

A notification fallback was triggered due to empty or invalid recipient configuration.

Details:
- Notification Type: {context.notification_type}
{entity_info}- Intended Recipients: {context.intended_recipients_count}
- Fallback Email: {FALLBACK_EMAIL}
- Timestamp: {datetime.utcnow().isoformat()}

ACTION REQUIRED:
Please check the notification_additional_recipients table configuration.
Add valid email recipients to ensure notifications are delivered properly.
        """
        
        try:
            # Send alert email to fallback address
            await self._email.send(FALLBACK_EMAIL, body, subject)
            logger.info(f"Fallback alert sent to {FALLBACK_EMAIL} for {context.notification_type}")
            
            # Update the fallback alert log entry status to SENT
            # Find the most recent fallback alert log for this notification type
            stmt = select(NotificationLog).where(
                NotificationLog.recipient_type == "FALLBACK_ALERT",
                NotificationLog.subject == "Notification Fallback Activated"
            ).order_by(NotificationLog.created_at.desc()).limit(1)
            
            log_entry = self._repo._session.exec(stmt).first()
            if log_entry:
                log_entry.status = "SENT"
                self._repo._session.add(log_entry)
                self._repo._session.commit()
                
        except Exception as e:
            logger.error(f"Failed to send fallback alert: {e}")
    
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
