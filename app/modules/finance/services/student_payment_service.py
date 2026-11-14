"""
app/modules/finance/services/student_payment_service.py
────────────────────────────────────────────────────────
Service for student payment operations.

Handles:
- Listing payments for a student
- Getting detailed payment information
- Queueing receipt notifications
"""
import logging
from typing import Optional


from app.db.uow import UnitOfWork
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.modules.finance.schemas import (
    PaymentWithDetailsDTO,
    PaginatedStudentPaymentsDTO,
    SendReceiptResultDTO,
)
from app.modules.finance.ports import PaymentNotifier
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import NotFoundError


logger = logging.getLogger(__name__)


class StudentPaymentService:
    """
    Service for student payment operations.
    
    Coordinates between finance repository and notification service
    to provide payment listing, details, and receipt sending.
    """
    
    def __init__(self, uow: UnitOfWork, notifier: Optional[PaymentNotifier] = None) -> None:
        self._uow = uow
        self._notifier = notifier
        self._payments = PaymentRepository(uow.session)
    
    def list_student_payments(
        self, student_id: int, skip: int = 0, limit: int = 50
    ) -> PaginatedStudentPaymentsDTO:
        """
        List all payments for a specific student.
        
        Args:
            student_id: The student's ID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            PaginatedStudentPaymentsDTO with payment items and total count
        """
        return self._payments.get_payments_by_student(
            student_id=student_id, skip=skip, limit=limit
        )
    
    def get_payment_details(self, payment_id: int) -> PaymentWithDetailsDTO:
        """
        Get comprehensive payment details including all related information.
        
        Args:
            payment_id: The payment ID
            
        Returns:
            PaymentWithDetailsDTO with complete payment information
            
        Raises:
            NotFoundError: If payment doesn't exist
        """
        result = self._payments.get_payment_with_details(payment_id)
        
        if result is None:
            raise NotFoundError(f"Payment ID {payment_id} not found.")
        
        return result
    
    def send_receipt(self, payment_id: int) -> SendReceiptResultDTO:
        """
        Queue the payment-received notification for a payment's receipt.

        The notifier sends to the system users configured for payment
        notifications, not to the student's parent.

        Raises:
            NotFoundError: If payment doesn't exist
        """
        payment = self._payments.get_payment_with_details(payment_id)
        if payment is None:
            raise NotFoundError(f"Payment ID {payment_id} not found.")

        if self._notifier:
            try:
                self._notifier.payment_received(
                    receipt_id=payment.receipt_id,
                    student_id=payment.student_id,
                    amount=f"{float(payment.amount):,.2f}",
                    receipt_number=payment.receipt_number or f"REC-{payment.receipt_id}",
                )
            except Exception:
                logger.exception("Payment notifier failed for receipt %s", payment.receipt_id)

        return SendReceiptResultDTO(
            success=True,
            message="Receipt notification queued.",
            receipt_id=payment.receipt_id,
            recipient_contact=None,
            sent_at=utc_now(),
        )
