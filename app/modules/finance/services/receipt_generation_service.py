"""
app/modules/finance/services/receipt_generation_service.py
─────────────────────────────────────────────────────────
Automated receipt generation with template support.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import text
from sqlmodel import select

from app.db.connection import get_session
from app.modules.finance import Receipt, Payment
from app.api.schemas.finance.receipt import BatchGenerateResponse, BatchReceiptItem
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.academics.models.group_models import Group
from app.modules.crm.models.student_models import Student
from app.shared.exceptions import NotFoundError


class ReceiptGenerationService:
    """Service for generating formatted receipts."""
    
    def __init__(self, db = None):
        """Initialize with optional database session."""
        self._db = db
        self._own_session = db is None
    
    def _get_db(self):
        """Get or create database session."""
        if self._db is None:
            self._db = get_session().__enter__()
        return self._db
    
    def __del__(self):
        """Cleanup session if owned."""
        if self._own_session and self._db:
            self._db.close()
    
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
        db = self._get_db()
        
        # Fetch receipt with all related data
        receipt = db.get(Receipt, receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with ID {receipt_id} not found")
        
        # Get payment lines for receipt
        payments_data = db.exec(
            select(Payment, Enrollment, Group)
            .outerjoin(Enrollment, Payment.enrollment_id == Enrollment.id)
            .outerjoin(Group, Enrollment.group_id == Group.id)
            .where(Payment.receipt_id == receipt_id)
        ).all()
        
        if not payments_data:
            raise NotFoundError(f"No payments found for receipt {receipt_id}")
        
        # Get student info from first payment
        first_payment = payments_data[0][0]
        student = db.get(Student, first_payment.student_id)
        
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
                from sqlalchemy import text
                result = db.execute(
                    text("""
                        SELECT COALESCE(SUM(balance), 0) as net_balance
                        FROM v_enrollment_balance
                        WHERE student_id = :sid
                    """),
                    {"sid": student.id}
                ).first()
                if result:
                    net_balance = float(result[0] or 0)
                    if net_balance < 0:
                        balance_remaining = abs(net_balance)
            except:
                pass  # Balance calculation failed, continue without
        
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
        payment: Payment,
        enrollment: Optional[Enrollment],
        group: Optional[Group]
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
        receipt: Receipt,
        student: Optional[Student],
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
        receipt: Receipt,
        student: Optional[Student],
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
    
    def mark_receipt_sent(
        self,
        receipt_id: int,
        parent_email: Optional[str] = None
    ) -> Receipt:
        """
        Mark a receipt as sent to parent.
        
        Args:
            receipt_id: Receipt ID
            parent_email: Email address receipt was sent to
            
        Returns:
            Updated receipt
        """
        db = self._get_db()
        
        receipt = db.get(Receipt, receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with ID {receipt_id} not found")
        
        receipt.sent_to_parent = True
        receipt.sent_at = datetime.utcnow()
        if parent_email:
            receipt.parent_email = parent_email
        
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        
        return receipt
    
    def generate_batch_receipts(
        self,
        receipt_ids: List[int],
        template_name: str = 'standard'
    ) -> List[BatchReceiptItem]:
        """Generate multiple receipts in batch with structured error handling."""
        db = self._get_db()
        results: List[BatchReceiptItem] = []
        
        for receipt_id in receipt_ids:
            try:
                receipt = db.get(Receipt, receipt_id)
                if not receipt:
                    results.append(BatchReceiptItem(
                        receipt_id=receipt_id,
                        success=False,
                        error_message=f"Receipt {receipt_id} not found",
                        error_code="not_found"
                    ))
                    continue
                
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

    def list_templates(self) -> List[Dict[str, Any]]:
        """List active receipt templates for admin selection."""
        db = self._get_db()
        rows = db.execute(
            text(
                """
                SELECT template_name, template_type, format, is_default, is_active, updated_at
                FROM receipt_templates
                WHERE is_active = TRUE
                ORDER BY is_default DESC, template_name ASC
                """
            )
        ).all()
        return [dict(row._mapping) for row in rows]

    def set_default_template(self, template_name: str) -> Dict[str, Any]:
        """Set one template as default and unset others."""
        db = self._get_db()
        exists = db.execute(
            text(
                """
                SELECT template_name
                FROM receipt_templates
                WHERE template_name = :name AND is_active = TRUE
                """
            ),
            {"name": template_name},
        ).first()
        if not exists:
            raise NotFoundError(f"Template '{template_name}' not found or inactive")

        db.execute(text("UPDATE receipt_templates SET is_default = FALSE WHERE is_default = TRUE"))
        db.execute(
            text(
                """
                UPDATE receipt_templates
                SET is_default = TRUE, updated_at = NOW()
                WHERE template_name = :name
                """
            ),
            {"name": template_name},
        )
        db.commit()
        return {"template_name": template_name, "is_default": True}


def get_receipt_generation_service(db = None):
    """Factory function to create ReceiptGenerationService instance."""
    return ReceiptGenerationService(db)
