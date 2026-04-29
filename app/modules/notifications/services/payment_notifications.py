"""
app/modules/notifications/services/payment_notifications.py
─────────────────────────────────────────────────────────────
Payment notification handlers.
"""
import logging
from typing import List, Optional, Tuple
from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService
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
        from app.modules.finance.models.receipt import Receipt
        from app.modules.finance.models.payment import Payment
        from app.modules.crm.models.student_models import Student
        from app.modules.academics.models.group_models import Group
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from sqlalchemy import select
        
        template = self._repo.get_template_by_name("payment_receipt")
        if not template or not template.is_active:
            logger.warning(f"Payment receipt template not found or inactive for receipt {receipt_id}")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "payment_received",
            entity_id=receipt_id,
            entity_description=f"Receipt #{receipt_number}"
        )
        
        # Fetch receipt
        receipt = self._repo._session.get(Receipt, receipt_id)
        if not receipt:
            logger.error(f"Receipt {receipt_id} not found")
            return
        
        # Fetch payment lines (receipt items)
        stmt = select(Payment).where(Payment.receipt_id == receipt_id)
        payment_lines = self._repo._session.exec(stmt).scalars().all()
        
        # Get student info
        student = self._repo._session.get(Student, student_id)
        student_name = student.full_name if student else f"Student #{student_id}"
        
        # Get group info from first payment line with enrollment
        group_name = "General Payment"
        instructor_name = "N/A"
        if payment_lines:
            first_payment = payment_lines[0]
            if first_payment.enrollment_id:
                enrollment = self._repo._session.get(Enrollment, first_payment.enrollment_id)
                if enrollment:
                    group = self._repo._session.get(Group, enrollment.group_id)
                    if group:
                        group_name = group.name
                        if group.instructor_id:
                            from app.modules.hr.models import Employee
                            instructor = self._repo._session.get(Employee, group.instructor_id)
                            if instructor:
                                instructor_name = instructor.full_name
        
        # Build rich variables for subject and body - use receipt object's fields
        actual_receipt_number = receipt.receipt_number or f"REC-{receipt.id}"
        actual_receipt_id = receipt.id
        # Use paid_at if available, otherwise created_at, otherwise fallback to current time
        if receipt.paid_at:
            payment_date = receipt.paid_at.strftime("%Y-%m-%d")
        elif receipt.created_at:
            payment_date = receipt.created_at.strftime("%Y-%m-%d")
        else:
            from datetime import datetime
            payment_date = datetime.now().strftime("%Y-%m-%d")
        
        # payment_method can be string or enum
        if receipt.payment_method:
            payment_method = receipt.payment_method.value if hasattr(receipt.payment_method, 'value') else str(receipt.payment_method)
        else:
            payment_method = "N/A"
        
        # Generate PDF attachment
        pdf_bytes = None
        try:
            from app.modules.finance.pdf.receipt_pdf import build_receipt_pdf
            pdf_bytes = build_receipt_pdf(
                receipt=receipt,
                lines=payment_lines,
                total=float(amount),
                payer_name=student_name,
                currency="EGP"
            )
            logger.info(f"Generated receipt PDF for receipt {actual_receipt_number}")
        except Exception as e:
            logger.error(f"Failed to generate receipt PDF: {e}")
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "amount": amount,
            "receipt_number": actual_receipt_number,
            "receipt_id": str(actual_receipt_id),
            "group_name": group_name,
            "instructor_name": instructor_name,
            "payment_date": payment_date,
            "payment_method": payment_method,
            "item_count": str(len(payment_lines)),
        }
        
        # Prepare attachments - use receipt.id as reliable fallback
        attachments = None
        if pdf_bytes:
            filename = f"receipt_{actual_receipt_number}.pdf"
            attachments = [(filename, pdf_bytes, "application/pdf")]
        
        # Send to all enabled recipients with PDF attachment
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(
                template, "EMAIL", recipient_type, recipient_id, email,
                variables, attachments=attachments
            )
    
    async def _process_reminder(self, student_id: int, amount_due: str, due_date: str) -> None:
        template = self._repo.get_template_by_name("payment_reminder")
        if not template or not template.is_active:
            logger.warning(f"Payment reminder template not found or inactive for student {student_id}")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "payment_reminder",
            entity_id=student_id,
            entity_description=f"Student #{student_id}"
        )
        
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
        
        # Send to all enabled recipients (fallback handled automatically by base service)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
