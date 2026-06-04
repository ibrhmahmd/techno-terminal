"""
app/modules/notifications/services/base_notification_service.py
─────────────────────────────────────────────────────────────
Base helpers for all notification services.
No business logic - just contact resolution, template rendering, dispatch.
"""
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlmodel import select

from app.core.config import settings

# Fallback email configuration
FALLBACK_EMAIL = settings.fallback_email
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
        self._background_tasks: set = set()

    # ── Session helper ───────────────────────────────────────────────────────

    def _new_session(self):
        """Context manager that opens a fresh DB session independent of the request lifecycle.
        Use this inside background task processors so they don't rely on the
        already-closed request session held in self._repo."""
        from app.db.connection import get_session
        return get_session()

    def _get_template_by_name(self, name: str) -> Optional["NotificationTemplate"]:
        """Fetch a notification template using a fresh session.

        MUST be used inside background task processors — self._repo holds the
        request-scoped session which is already closed by the time any
        BackgroundTask runs.
        """
        with self._new_session() as session:
            from app.modules.notifications.repositories.notification_repository import NotificationRepository
            fresh_repo = NotificationRepository(session)
            return fresh_repo.get_template_by_name(name)

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
        with self._new_session() as session:
            student = session.get(Student, student_id)
            if not student:
                return None, None, "", ""

            # Get primary parent
            stmt = select(Parent, StudentParent).join(StudentParent).where(
                StudentParent.student_id == student_id,
                StudentParent.is_primary.is_(True),
            )
            result = session.exec(stmt).first()

            # Fallback to any parent
            if not result:
                stmt2 = select(Parent, StudentParent).join(StudentParent).where(
                    StudentParent.student_id == student_id
                )
                result = session.exec(stmt2).first()

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

        # Get all active additional recipients for this notification type where the admin has it enabled
        try:
            stmt = text("""
                SELECT nar.id, nar.email
                FROM notification_additional_recipients nar
                JOIN admin_notification_settings ans
                    ON ans.admin_id = nar.admin_id
                    AND ans.notification_type = :notification_type
                    AND ans.is_enabled = true
                WHERE nar.is_active = true
                AND (nar.notification_types IS NULL OR :notification_type = ANY(nar.notification_types))
            """)
            with self._new_session() as session:
                result = session.execute(stmt, params={"notification_type": notification_type}).all()
            for recipient_id, email in result:
                if email and self._is_valid_email(email):
                    recipients.append((email, recipient_id, "EMPLOYEE"))
                elif email:
                    invalid_emails_found.append((recipient_id, email))
        except Exception as e:
            logger.error(f"Failed to fetch additional recipients: {e}")

        # Check if we need to trigger fallback
        if not recipients:
            # Validate and use fallback email
            if self._is_valid_email(FALLBACK_EMAIL):
                recipients.append((FALLBACK_EMAIL, FALLBACK_RECIPIENT_ID, "EMPLOYEE"))

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
                        recipient_type="EMPLOYEE",
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
                    intended_recipients_count=len(invalid_emails_found)
                )
                try:
                    import asyncio
                    task = asyncio.create_task(self._send_fallback_alert(context))
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
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
    
    def _get_group_name(self, group_id: int) -> str:
        from app.modules.academics.models import Group
        with self._new_session() as session:
            group = session.get(Group, group_id)
        return group.name if group else "Unknown Group"

    def _get_instructor_name(self, group_id: int) -> str:
        from app.modules.academics.models import Group
        from app.modules.hr.models import Employee
        with self._new_session() as session:
            group = session.get(Group, group_id)
            if group and group.instructor_id:
                instructor = session.get(Employee, group.instructor_id)
                return instructor.full_name if instructor else "Unknown"
        return "Unknown"

    def _get_student_name(self, student_id: int) -> str:
        from app.modules.crm.models.student_models import Student
        with self._new_session() as session:
            student = session.get(Student, student_id)
        return student.full_name if student else f"Student #{student_id}"

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
            entity_info += f'<p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 140px;">Entity ID</span> <strong>{context.entity_id}</strong></p>'
        if context.entity_description:
            entity_info += f'<p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 140px;">Entity Description</span> <strong>{context.entity_description}</strong></p>'
        
        body = f"""<html>
<body style="background-color: #f8f9ff; font-family: 'Inter', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #e11d48; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids Diagnostics</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #e11d48;">Notification Fallback Activated</h2>
      <p style="line-height: 1.6;">A notification fallback was triggered because no valid active recipients were found for this event type.</p>
      
      <div style="background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #e11d48;">Event Details</p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 140px;">Notification Type</span> <strong>{context.notification_type}</strong></p>
        {entity_info}
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 140px;">Intended Recipients</span> <strong>{context.intended_recipients_count}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 140px;">Fallback Email</span> <strong>{FALLBACK_EMAIL}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 140px;">Timestamp (UTC)</span> <strong>{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}</strong></p>
      </div>
      
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 16px; border-radius: 4px; margin-top: 24px;">
        <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #0f172a;">Action Required</p>
        <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #475569;">Please verify your <code style="background: #e2e8f0; padding: 2px 4px; border-radius: 4px;">notification_additional_recipients</code> configuration. Ensure emails are correct and marked as active.</p>
      </div>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>"""
        
        try:
            # Send alert email to fallback address
            await self._email.send(FALLBACK_EMAIL, body, subject)
            logger.info(f"Fallback alert sent to {FALLBACK_EMAIL} for {context.notification_type}")
            
            # Update the fallback alert log entry status to SENT
            # Find the most recent fallback alert log for this notification type
            stmt = select(NotificationLog).where(
                NotificationLog.recipient_type == "EMPLOYEE",
                NotificationLog.subject == "Notification Fallback Activated"
            ).order_by(NotificationLog.created_at.desc()).limit(1)

            with self._new_session() as session:
                log_entry = session.exec(stmt).first()
                if log_entry:
                    log_entry.status = "SENT"
                    session.add(log_entry)
                    session.commit()
                
        except Exception as e:
            logger.error(f"Failed to send fallback alert: {e}")
    
    async def dispatch_notification(
        self, template: NotificationTemplate, channel: str, recipient_type: str,
        recipient_id: int, contact: str, variables: dict,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None
    ) -> None:
        """Public wrapper for _dispatch."""
        await self._dispatch(
            template, channel, recipient_type, recipient_id, contact, variables, attachments
        )

    async def _dispatch(
        self, template: NotificationTemplate, channel: str, recipient_type: str,
        recipient_id: int, contact: str, variables: dict,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None
    ) -> None:
        """Send notification and log result.
        
        Args:
            template: Notification template
            channel: "EMAIL" or "WHATSAPP"
            recipient_type: "PARENT" or "EMPLOYEE" (must match DB CHECK constraint)
            recipient_id: ID of recipient
            contact: Email address or phone number
            variables: Template variable substitutions
            attachments: Optional list of (filename, bytes, mimetype) for email attachments
        """
        body = self._render_template(template, variables)
        
        subject = None
        if template.subject:
            subject = template.subject
            for key, val in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(val))
        
        # Create log entry in a fresh session (non-blocking — log failures won't block email delivery)
        log_id = None
        try:
            from app.modules.notifications.repositories.notification_repository import NotificationRepository
            with self._new_session() as log_session:
                log_repo = NotificationRepository(log_session)
                log = log_repo.create_log(
                    template_id=template.id,
                    channel=channel,
                    recipient_type=recipient_type,
                    recipient_id=recipient_id,
                    recipient_contact=contact,
                    body=body,
                    subject=subject,
                )
                log_session.commit()
                log_id = log.id
        except Exception as log_error:
            logger.warning(f"Failed to create notification log: {log_error}")
        
        # Dispatch (WhatsApp disabled - email only for now)
        success, error = False, "Unknown channel"
        if channel == "WHATSAPP":
            logger.info(f"WhatsApp notifications disabled - skipping message to {recipient_type} {recipient_id}")
            success = True  # Mark as success to avoid retry attempts
        elif channel == "EMAIL":
            success, error = await self._email.send(contact, body, subject, attachments)
        
        # Update log status in a fresh session
        if log_id:
            try:
                with self._new_session() as log_session:
                    from app.modules.notifications.repositories.notification_repository import NotificationRepository
                    log_repo = NotificationRepository(log_session)
                    status = "SENT" if success else "FAILED"
                    log_repo.update_log_status(log_id, status, error)
                    log_session.commit()
            except Exception as update_error:
                logger.warning(f"Failed to update notification log status: {update_error}")

        if success:
            logger.info(f"Notification sent to {recipient_type} {recipient_id} via {channel}")
        else:
            logger.error(f"Notification failed to {recipient_type} {recipient_id}: {error}")
