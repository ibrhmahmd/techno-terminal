"""
app/modules/finance/services/receipt_generation_service.py
─────────────────────────────────────────────────────────
Automated receipt generation with template support.
"""
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from decimal import Decimal

from app.db.uow import UnitOfWork
from app.modules.finance.repositories.receipt_document_repository import ReceiptDocumentRepository
from app.modules.finance.schemas.receipt_generation import BatchGenerateResponse, BatchReceiptItem
from app.shared.exceptions import NotFoundError

if TYPE_CHECKING:
    from app.modules.academics.models.group_models import Group
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.crm.models.student_models import Student
    from app.modules.finance.models import Payment, Receipt

logger = logging.getLogger(__name__)


class ReceiptGenerationService:
    """Service for generating formatted receipts."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._receipts = ReceiptDocumentRepository(uow.session)

    def generate_receipt_text(
        self,
        receipt_id: int,
        template_name: str = 'standard',
        include_balance: bool = True
    ) -> str:
        """
        Generate a text receipt from receipt data.
        
        Args:
            receipt_id: Receipt ID to generate
            template_name: Template to use (standard, detailed)
            include_balance: Include remaining balance
            
        Returns:
            Formatted receipt text
        """
        # Fetch receipt with all related data
        receipt = self._receipts.get_receipt(receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with ID {receipt_id} not found")
            
        # Get payment lines for receipt
        payments_data = self._receipts.get_payment_rows_with_group(receipt_id)
            
        if not payments_data:
            raise NotFoundError(f"No payments found for receipt {receipt_id}")
            
        # Get student info from first payment
        first_payment = payments_data[0][0]
        student = self._receipts.get_student(first_payment.student_id)
            
        # Build payment lines
        payment_lines = []
        total_discount = Decimal('0.00')
            
        for payment, enrollment, group in payments_data:
            description = self._build_description(payment, enrollment, group)
                
            line_discount = Decimal(str(payment.discount_amount or 0))
            total_discount += line_discount
                
            payment_lines.append({
                'description': description,
                'amount': float(payment.amount),
                'discount': float(line_discount),
                'net_amount': float(Decimal(str(payment.amount)) - line_discount)
            })
            
        # Calculate totals
        subtotal = sum(line['amount'] for line in payment_lines)
        total = subtotal - float(total_discount)
            
        # Get balance if requested (query v_enrollment_balance directly)
        balance_remaining = 0.0
        if include_balance and student:
            try:
                net_balance = self._receipts.get_student_net_balance(student.id)
                if net_balance < 0:
                    balance_remaining = abs(net_balance)
            except Exception:
                logger.warning("Balance query failed for student %s — continuing without balance", student.id)
            
        # Render based on template
        if template_name == 'detailed':
            return self._render_detailed_template(
                receipt=receipt,
                student=student,
                payment_lines=payment_lines,
                subtotal=subtotal,
                total_discount=float(total_discount),
                total=total,
                balance_remaining=balance_remaining
            )
        else:
            return self._render_standard_template(
                receipt=receipt,
                student=student,
                payment_lines=payment_lines,
                subtotal=subtotal,
                total_discount=float(total_discount),
                total=total,
                balance_remaining=balance_remaining
            )
    
    def _build_description(
        self,
        payment: "Payment",
        enrollment: Optional["Enrollment"],
        group: Optional["Group"]
    ) -> str:
        """Build human-readable payment description."""
        
        if payment.payment_type == 'course_level' and enrollment and group:
            return f"Course Fee - {group.name} (Level {enrollment.level_number})"
        elif payment.payment_type == 'competition':
            return "Competition Fee"
        elif payment.payment_type == 'refund':
            return "Refund"
        elif payment.transaction_type == 'charge':
            return "Additional Charge"
        else:
            return "Payment"
    
    def _render_standard_template(
        self,
        receipt: "Receipt",
        student: Optional["Student"],
        payment_lines: List[Dict[str, Any]],
        subtotal: float,
        total_discount: float,
        total: float,
        balance_remaining: float
    ) -> str:
        """Render standard receipt template."""
        
        lines_text = "\n".join([
            f"{line['description'][:40].ljust(40)} ${line['amount']:.2f}"
            for line in payment_lines
        ])
        
        balance_section = ""
        if balance_remaining > 0:
            balance_section = f"\nRemaining Balance: ${balance_remaining:.2f}\n"
        
        template = f"""
{'='*50}
RECEIPT #: {receipt.receipt_number or 'N/A'}
Date: {receipt.paid_at.strftime('%Y-%m-%d %H:%M') if receipt.paid_at else 'N/A'}
{'='*50}

Student: {student.full_name if student else 'Unknown'}
Payer: {receipt.payer_name or (student.full_name if student else 'Unknown')}

{'-'*50}
DESCRIPTION{' '*31}AMOUNT
{'-'*50}
{lines_text}
{'-'*50}
Subtotal:{' '*38}${subtotal:.2f}
Discount:{' '*38}${total_discount:.2f}
{'-'*50}
TOTAL PAID:{' '*36}${total:.2f}
{'-'*50}

Payment Method: {receipt.payment_method or 'N/A'}
{balance_section}
Thank you for your payment!
{'='*50}
"""
        
        return template.strip()
    
    def _render_detailed_template(
        self,
        receipt: "Receipt",
        student: Optional["Student"],
        payment_lines: List[Dict[str, Any]],
        subtotal: float,
        total_discount: float,
        total: float,
        balance_remaining: float
    ) -> str:
        """Render detailed receipt template."""
        
        items_text = "\n\n".join([
            f"Item: {line['description']}\n"
            f"  Amount: ${line['amount']:.2f}\n"
            f"  Discount: ${line['discount']:.2f}\n"
            f"  Net: ${line['net_amount']:.2f}"
            for line in payment_lines
        ])
        
        balance_section = ""
        if balance_remaining > 0:
            balance_section = f"\nREMAINING BALANCE: ${balance_remaining:.2f}\n"
        
        template = f"""
{'='*50}
DETAILED RECEIPT #: {receipt.receipt_number or 'N/A'}
Date: {receipt.paid_at.strftime('%Y-%m-%d %H:%M') if receipt.paid_at else 'N/A'}
{'='*50}

STUDENT INFORMATION
{'-'*50}
Name: {student.full_name if student else 'Unknown'}
Student ID: {student.id if student else 'N/A'}

PAYMENT DETAILS
{'-'*50}
{items_text}
{'-'*50}
Subtotal:{' '*38}${subtotal:.2f}
Total Discounts:{' '*32}${total_discount:.2f}
{'-'*50}
TOTAL PAID:{' '*36}${total:.2f}
{'-'*50}

Payment Method: {receipt.payment_method or 'N/A'}
Receipt #: {receipt.receipt_number or 'N/A'}
{balance_section}
This receipt was generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}.
{'='*50}
"""
        
        return template.strip()
    
    def generate_batch_receipts(
        self,
        receipt_ids: List[int],
        template_name: str = 'standard'
    ) -> List[BatchReceiptItem]:
        """Generate multiple receipts in batch with structured error handling."""
        results: List[BatchReceiptItem] = []
        
        for receipt_id in receipt_ids:
            try:
                receipt = self._receipts.get_receipt(receipt_id)
                if not receipt:
                    results.append(BatchReceiptItem(
                        receipt_id=receipt_id,
                        success=False,
                        error_message=f"Receipt {receipt_id} not found",
                        error_code="not_found"
                    ))
                    continue
                
                # generate_receipt_text creates its own session
                content = self.generate_receipt_text(receipt_id, template_name)
                results.append(BatchReceiptItem(
                    receipt_id=receipt_id,
                    success=True,
                    content=content
                ))
            except NotFoundError as e:
                results.append(BatchReceiptItem(
                    receipt_id=receipt_id,
                    success=False,
                    error_message=str(e),
                    error_code="not_found"
                ))
            except Exception as e:
                results.append(BatchReceiptItem(
                    receipt_id=receipt_id,
                    success=False,
                    error_message=str(e),
                    error_code="generation_failed"
                ))
        
        return results



