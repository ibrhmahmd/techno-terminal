import logging
from typing import Optional, Dict, Any, Tuple, List
from fastapi import BackgroundTasks
from sqlmodel import select

from app.modules.notifications.interfaces.i_notification_repository import INotificationRepository
from app.modules.notifications.dispatchers.whatsapp_dispatcher import TwilioWhatsAppDispatcher
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.models.notification_template import NotificationTemplate

from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent
from app.modules.crm.models.student_models import Student

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Main notification orchestrator.
    """

    def __init__(self, repo: INotificationRepository):
        self._repo = repo
        self._whatsapp = TwilioWhatsAppDispatcher()
        self._email = GmailEmailDispatcher()

    # ── Transactional (called by other services) ─────────────────────────
    def notify_absence(self, student_id: int, session_name: str, session_date: str, background_tasks: BackgroundTasks) -> None:
        """Queues an absence alert to the student's primary parent. Non-blocking."""
        background_tasks.add_task(
            self._process_absence_notification,
            student_id, session_name, session_date
        )

    def notify_enrollment(self, enrollment_id: int, student_id: int, group_id: int, background_tasks: BackgroundTasks) -> None:
        """Queues an enrollment confirmation to the student's primary parent."""
        background_tasks.add_task(
            self._process_enrollment_notification, 
            enrollment_id, student_id, group_id
        )

    def notify_payment_receipt(self, receipt_id: int, student_id: int, amount: str, receipt_number: str, background_tasks: BackgroundTasks) -> None:
        """Queues a payment receipt notification to the parent."""
        background_tasks.add_task(
            self._process_receipt_notification, 
            receipt_id, student_id, amount, receipt_number
        )

    # ── Scheduled Reports ────────────────────────────────────────────────────
    async def send_daily_report(self) -> None:
        logger.info("Sending daily business report.")
        # Stub for future analytics integration
        pass

    async def send_weekly_report(self) -> None:
        logger.info("Sending weekly business report.")
        pass

    async def send_monthly_report(self) -> None:
        logger.info("Sending monthly business report.")
        pass

    # ── Bulk Marketing ────────────────────────────────────────────────────────
    def send_bulk(self, parent_ids: list[int], template_name: str, extra_vars: dict, background_tasks: BackgroundTasks) -> int:
        """Queues WhatsApp messages to a list of parents. Returns queued count."""
        template = self._repo.get_template_by_name(template_name)
        if not template or not template.is_active:
            return 0
            
        count = 0
        for pid in parent_ids:
            background_tasks.add_task(self._process_bulk_item, pid, template, extra_vars)
            count += 1
        return count

    # ── Asynchronous Processors ──────────────────────────────────────────────
    async def _process_absence_notification(self, student_id: int, session_name: str, session_date: str) -> None:
        template = self._repo.get_template_by_name("absence_alert")
        if not template or not template.is_active:
            return

        phone, parent_id, parent_name, student_name = self._resolve_contact_info(student_id)
        if not phone or not parent_id:
            return

        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "session_name": session_name,
            "session_date": session_date
        }
        await self._dispatch_internal(template, "WHATSAPP", "PARENT", parent_id, phone, variables)

    async def _process_enrollment_notification(self, enrollment_id: int, student_id: int, group_id: int) -> None:
        template = self._repo.get_template_by_name("enrollment_confirmation")
        if not template or not template.is_active:
            return

        phone, parent_id, parent_name, student_name = self._resolve_contact_info(student_id)
        if not phone or not parent_id:
            return

        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "group_name": f"Group {group_id}", 
            "course_name": f"Course via Group {group_id}"
        }
        await self._dispatch_internal(template, "WHATSAPP", "PARENT", parent_id, phone, variables)

    async def _process_receipt_notification(self, receipt_id: int, student_id: int, amount: str, receipt_number: str) -> None:
        template = self._repo.get_template_by_name("payment_receipt")
        if not template or not template.is_active:
            return
        
        phone, parent_id, parent_name, student_name = self._resolve_contact_info(student_id)
        if not phone or not parent_id:
            return

        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "amount": amount,
            "receipt_number": receipt_number
        }
        await self._dispatch_internal(template, "WHATSAPP", "PARENT", parent_id, phone, variables)

    async def _process_bulk_item(self, parent_id: int, template: NotificationTemplate, extra_vars: dict) -> None:
        parent = self._repo._session.get(Parent, parent_id)
        if not parent or not parent.phone_primary:
            return
            
        variables = extra_vars.copy()
        variables.setdefault("parent_name", parent.full_name)
        await self._dispatch_internal(template, "WHATSAPP", "PARENT", parent_id, parent.phone_primary, variables)

    # ── Private helpers ──────────────────────────────────────────────────
    def _render(self, template: NotificationTemplate, variables: dict) -> str:
        """Simple {{key}} substitution."""
        body = template.body
        for key, val in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
        return body

    def _resolve_contact_info(self, student_id: int) -> Tuple[Optional[str], Optional[int], str, str]:
        """Returns (phone, parent_id, parent_name, student_name)."""
        student = self._repo._session.get(Student, student_id)
        if not student:
            return None, None, "", ""

        stmt = select(Parent, StudentParent).join(StudentParent).where(
            StudentParent.student_id == student_id,
            StudentParent.is_primary == True
        )
        result = self._repo._session.exec(stmt).first()
        
        # Fallback to any parent if no primary link exists
        if not result:
            stmt2 = select(Parent, StudentParent).join(StudentParent).where(
                StudentParent.student_id == student_id
            )
            result = self._repo._session.exec(stmt2).first()
            
        if result:
            parent, _ = result
            return parent.phone_primary, parent.id, parent.full_name, student.full_name
            
        return None, None, "", student.full_name

    async def _dispatch_internal(
        self, template: NotificationTemplate, default_channel: str, 
        recipient_type: str, recipient_id: int, contact: str, variables: dict
    ) -> None:
        channel = template.channel or default_channel
        body = self._render(template, variables)
        subject_rendered = self._render(template, variables) if template.subject else None

        # Synchronously write the log record
        log = self._repo.create_log(
            template_id=template.id,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            recipient_contact=contact,
            body=body,
            subject=subject_rendered
        )

        # Dispatch via proper dispatcher
        success, error = False, "Unknown Channel"
        if channel == "WHATSAPP":
            success, error = await self._whatsapp.send(contact, body)
        elif channel == "EMAIL":
            success, error = await self._email.send(contact, body, subject_rendered)

        # Update log with result
        status = "SENT" if success else "FAILED"
        self._repo.update_log_status(log.id, status, error)
