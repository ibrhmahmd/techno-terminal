"""
app/modules/notifications/services/payment_notifications.py
─────────────────────────────────────────────────────────────
Payment notification handlers.
"""
import logging
from typing import Optional
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
        from sqlmodel import select
        from app.db.connection import get_session

        template = self._get_template_by_name("payment_receipt")
        if not template or not template.is_active:
            logger.warning(f"Payment receipt template not found or inactive for receipt {receipt_id}")
            return

        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "payment_received",
            entity_id=receipt_id,
            entity_description=f"Receipt #{receipt_number}"
        )

        # Open a fresh session — the request session is already closed by the time
        # this background task executes.
        with get_session() as session:
            # Fetch receipt
            receipt = session.get(Receipt, receipt_id)
            if not receipt:
                logger.error(f"Receipt {receipt_id} not found")
                return

            # Fetch payment lines (receipt items)
            stmt = select(Payment).where(Payment.receipt_id == receipt_id)
            payment_lines = list(session.exec(stmt).all())

            # Get student info
            student = session.get(Student, student_id)
            student_name = student.full_name if student else f"Student #{student_id}"

            # Get group info from first payment line with enrollment
            group_name = "General Payment"
            instructor_name = "N/A"
            if payment_lines:
                first_payment = payment_lines[0]
                if first_payment.enrollment_id:
                    enrollment = session.get(Enrollment, first_payment.enrollment_id)
                    if enrollment:
                        group = session.get(Group, enrollment.group_id)
                        if group:
                            group_name = group.name
                            if group.instructor_id:
                                from app.modules.hr.models import Employee
                                instructor = session.get(Employee, group.instructor_id)
                                if instructor:
                                    instructor_name = instructor.full_name

            # Build rich variables for subject and body - use receipt object's fields
            actual_receipt_number = receipt.receipt_number or f"REC-{receipt.id}"
            actual_receipt_id = receipt.id
            
            from datetime import datetime
            dt_obj = receipt.paid_at or receipt.created_at or datetime.now()
            payment_date = dt_obj.strftime("%Y-%m-%d")
            payment_time = dt_obj.strftime("%H:%M")

            # payment_method can be string or enum
            if receipt.payment_method:
                payment_method = receipt.payment_method.value if hasattr(receipt.payment_method, 'value') else str(receipt.payment_method)
            else:
                payment_method = "N/A"
                
            # Location and Device
            pm_lower = payment_method.lower()
            if pm_lower in ["card", "online", "stripe", "bank_transfer"]:
                location = "Online Portal"
                device = "Web Client"
            else:
                location = "KFS Branch"
                device = "Reception Desktop POS"
                
            transaction_reference = f"TXN-{actual_receipt_id}-{dt_obj.strftime('%M%S')}"
            
            # Fetch Processed By Info
            processed_by_name = "System Auto"
            processed_by_role = "System"
            from app.modules.auth.models.auth_models import User
            from app.modules.hr.models.employee_models import Employee
            if receipt.received_by:
                user = session.get(User, receipt.received_by)
                if user:
                    processed_by_name = user.email.split('@')[0] if user.email else f"User {user.id}"
                    processed_by_role = str(getattr(user, 'role', 'Admin'))
                    # Attempt to fetch Employee
                    stmt_emp = select(Employee).where(Employee.user_id == user.id)
                    employee = session.exec(stmt_emp).first()
                    if employee:
                        processed_by_name = employee.full_name
                        processed_by_role = employee.job_title or processed_by_role

            # Fetch Remaining Balance
            balance_remaining = 0.0
            try:
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT COALESCE(SUM(balance), 0) FROM v_enrollment_balance WHERE student_id = :sid"),
                    {"sid": student.id}
                ).first()
                if result:
                    net_balance = float(result[0] or 0)
                    if net_balance < 0:
                        balance_remaining = abs(net_balance)
            except Exception:
                pass

            # Generate PDF attachment
            pdf_bytes = None
            try:
                from app.modules.finance.pdf.receipt_pdf import build_receipt_pdf
                pdf_bytes = build_receipt_pdf(
                    receipt=receipt,
                    lines=payment_lines,
                    total=float(amount),
                    payer_name=student_name,
                    currency="EGP",
                    processed_by=f"{processed_by_name} ({processed_by_role})",
                    location=location,
                    device=device,
                    transaction_ref=transaction_reference,
                    balance_remaining=balance_remaining,
                    payment_time=payment_time
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
                "payment_time": payment_time,
                "payment_method": payment_method,
                "location": location,
                "device": device,
                "processed_by": processed_by_name,
                "processed_role": processed_by_role,
                "transaction_ref": transaction_reference,
                "balance_remaining": f"{balance_remaining:.2f}",
                "item_count": str(len(payment_lines)),
            }

            # Prepare attachments - use receipt.id as reliable fallback
            attachments = None
            if pdf_bytes:
                clean_student = "".join(c for c in student_name if c.isalnum() or c in " _-").replace(' ', '_')
                clean_group = "".join(c for c in group_name if c.isalnum() or c in " _-").replace(' ', '_')
                clean_time = payment_time.replace(':', '')
                filename = f"Receipt_{clean_student}_{clean_group}_{amount}EGP_{payment_date}_{clean_time}.pdf"
                attachments = [(filename, pdf_bytes, "application/pdf")]

        # Send to all enabled recipients with PDF attachment
        # (outside session context — dispatch uses its own I/O)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(
                template, "EMAIL", recipient_type, recipient_id, email,
                variables, attachments=attachments
            )

    async def _process_reminder(self, student_id: int, amount_due: str, due_date: str) -> None:
        template = self._get_template_by_name("payment_reminder")
        if not template or not template.is_active:
            logger.warning(f"Payment reminder template not found or inactive for student {student_id}")
            return

        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "payment_reminder",
            entity_id=student_id,
            entity_description=f"Student #{student_id}"
        )

        # Open a fresh session for background task execution
        from app.db.connection import get_session
        from app.modules.crm.models.student_models import Student
        with get_session() as session:
            student = session.get(Student, student_id)
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

