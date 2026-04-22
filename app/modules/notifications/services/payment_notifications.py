"""
app/modules/notifications/services/payment_notifications.py
─────────────────────────────────────────────────────────────
Payment notification handlers.
"""
import logging
from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService, FALLBACK_RECIPIENT_ID
from app.modules.notifications.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class PaymentNotificationService(BaseNotificationService):
    """Handles: payment received, payment reminders, receipt."""
    
    def __init__(self, repo: NotificationRepository):
        super().__init__(repo)
    
    def notify_payment_received(
        self, receipt_id: int, student_id: int, amount: str,
        receipt_number: str, background_tasks: BackgroundTasks
    ) -> None:
        """Payment confirmation receipt."""
        background_tasks.add_task(
            self._process_received, receipt_id, student_id, amount, receipt_number
        )
    
    def notify_payment_reminder(
        self, student_id: int, amount_due: str, due_date: str,
        background_tasks: BackgroundTasks
    ) -> None:
        """Payment due reminder."""
        background_tasks.add_task(
            self._process_reminder, student_id, amount_due, due_date
        )
    
    # ── Private Processors ─────────────────────────────────────────────────
    
    async def _process_received(self, receipt_id: int, student_id: int,
                                 amount: str, receipt_number: str) -> None:
        template = self._repo.get_template_by_name("payment_receipt")
        if not template or not template.is_active:
            logger.warning(f"Payment receipt template not found or inactive for receipt {receipt_id}")
            return
        
        # Get notification recipients based on admin settings
        recipients = self._resolve_notification_recipients("payment_received")
        
        # Check if fallback was triggered
        fallback_triggered = any(r[2] == "FALLBACK" for r in recipients)
        if fallback_triggered:
            logger.warning(f"FALLBACK ACTIVE: Sending payment receipt {receipt_id} to fallback email")
        
        # Get student info for variables
        from app.modules.crm.models.student_models import Student
        student = self._repo._session.get(Student, student_id)
        student_name = student.full_name if student else f"Student #{student_id}"
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "amount": amount,
            "receipt_number": receipt_number,
            "receipt_id": str(receipt_id),
        }
        
        # Send to all enabled recipients (includes fallback if triggered)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
            
        # If fallback triggered, also send alert notification to fallback email
        if fallback_triggered:
            await self._send_fallback_alert("payment_received", receipt_id, len(recipients) - 1)
    
    async def _process_reminder(self, student_id: int, amount_due: str, due_date: str) -> None:
        template = self._repo.get_template_by_name("payment_reminder")
        if not template or not template.is_active:
            logger.warning(f"Payment reminder template not found or inactive for student {student_id}")
            return
        
        # Get notification recipients based on admin settings
        recipients = self._resolve_notification_recipients("payment_reminder")
        
        # Check if fallback was triggered
        fallback_triggered = any(r[2] == "FALLBACK" for r in recipients)
        if fallback_triggered:
            logger.warning(f"FALLBACK ACTIVE: Sending payment reminder to fallback email for student {student_id}")
        
        # Get student info for variables
        from app.modules.crm.models.student_models import Student
        student = self._repo._session.get(Student, student_id)
        student_name = student.full_name if student else f"Student #{student_id}"
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "amount_due": amount_due,
            "due_date": due_date,
        }
        
        # Send to all enabled recipients (includes fallback if triggered)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
            
        # If fallback triggered, also send alert notification to fallback email
        if fallback_triggered:
            await self._send_fallback_alert("payment_reminder", student_id, len(recipients) - 1)
