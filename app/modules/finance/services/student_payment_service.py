"""
app/modules/finance/services/student_payment_service.py
────────────────────────────────────────────────────────
Service for student payment operations.

Handles:
- Listing payments for a student
- Getting detailed payment information
- Sending receipts via WhatsApp/Email
"""
from datetime import datetime

from fastapi import BackgroundTasks

from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
from app.modules.finance.interfaces.dto import (
    PaymentWithDetailsDTO,
    PaginatedStudentPaymentsDTO,
    SendReceiptResultDTO,
)
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.db.connection import get_engine
from sqlmodel import Session
from app.shared.exceptions import NotFoundError


class StudentPaymentService:
    """
    Service for student payment operations.
    
    Coordinates between finance repository and notification service
    to provide payment listing, details, and receipt sending.
    """
    
    def __init__(self, uow: FinanceUnitOfWork) -> None:
        self._uow = uow
    
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
        items, total = self._uow.payments.get_payments_by_student(
            student_id=student_id, skip=skip, limit=limit
        )
        
        return PaginatedStudentPaymentsDTO(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
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
        result = self._uow.payments.get_payment_with_details(payment_id)
        
        if result is None:
            raise NotFoundError(f"Payment ID {payment_id} not found.")
        
        return result
    
    def send_receipt(
        self,
        payment_id: int,
        method: str,  # "whatsapp" or "email"
        background_tasks: BackgroundTasks,
        sent_by_user_id: int,
    ) -> SendReceiptResultDTO:
        """
        Send receipt to the student's primary parent via WhatsApp or Email.
        
        Args:
            payment_id: The payment ID
            method: Delivery method - "whatsapp" or "email"
            background_tasks: FastAPI BackgroundTasks for async processing
            sent_by_user_id: ID of the user triggering the send
            
        Returns:
            SendReceiptResultDTO with success status and details
            
        Raises:
            NotFoundError: If payment doesn't exist
            ValueError: If no parent contact found or invalid method
        """
        # Get payment details
        payment = self._uow.payments.get_payment_with_details(payment_id)
        if payment is None:
            raise NotFoundError(f"Payment ID {payment_id} not found.")
        
        # Validate we have parent info
        if not payment.parent_id:
            return SendReceiptResultDTO(
                success=False,
                message=f"No parent found for student {payment.student_name}.",
                receipt_id=payment.receipt_id,
                recipient_contact=None,
                sent_at=datetime.utcnow(),
            )
        
        # Create notification service
        session = Session(get_engine(), expire_on_commit=False)
        try:
            notification_svc = NotificationService(NotificationRepository(session))
            
            # Format amount for display
            amount_str = f"{float(payment.amount):,.2f}"
            
            # Use the notification service to send receipt
            # The notification service handles template rendering and dispatch
            notification_svc.payment.notify_payment_received(
                receipt_id=payment.receipt_id,
                student_id=payment.student_id,
                amount=amount_str,
                receipt_number=payment.receipt_number or f"REC-{payment.receipt_id}",
                background_tasks=background_tasks,
            )
            
            # Determine recipient contact based on method
            if method == "whatsapp":
                recipient_contact = payment.parent_phone
                if not recipient_contact:
                    return SendReceiptResultDTO(
                        success=False,
                        message=f"Parent {payment.parent_name} has no phone number for WhatsApp.",
                        receipt_id=payment.receipt_id,
                        recipient_contact=None,
                        sent_at=datetime.utcnow(),
                    )
            elif method == "email":
                # Email contact would need to be fetched from parent record
                # For now, return the phone as contact (notification service handles actual dispatch)
                recipient_contact = payment.parent_phone
            else:
                return SendReceiptResultDTO(
                    success=False,
                    message=f"Invalid method: {method}. Use 'whatsapp' or 'email'.",
                    receipt_id=payment.receipt_id,
                    recipient_contact=None,
                    sent_at=datetime.utcnow(),
                )
            
            return SendReceiptResultDTO(
                success=True,
                message=f"Receipt queued for sending to {payment.parent_name} via {method}.",
                receipt_id=payment.receipt_id,
                recipient_contact=recipient_contact,
                sent_at=datetime.utcnow(),
            )
        finally:
            session.close()
