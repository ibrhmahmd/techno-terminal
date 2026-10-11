"""
app/modules/finance/services/refund_service.py
───────────────────────────────────────────
Refund service implementation with atomic transaction handling.
"""
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.crm import StudentActivityService

from app.modules.finance.schemas import (
    RefundResultDTO,
    IssueRefundDTO,
)
from app.db.uow import UnitOfWork
from app.modules.crm import LogPaymentDTO
from app.modules.finance.repositories.receipt_repository import ReceiptRepository
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.finance.schemas import CreateReceiptDTO
from app.modules.finance.schemas import AddPaymentLineDTO
from app.modules.finance.models.payment import Payment
from sqlalchemy import select


class RefundService:
    """
    Service for refund business operations.

    Responsible for:
    - Processing refunds against original payments
    - Validating refund amounts don't exceed original
    - Atomic receipt creation with refund line
    - Competition fee unmarking (if applicable)
    """

    def __init__(
        self,
        uow: UnitOfWork,
        activity_svc: Optional["StudentActivityService"] = None,
    ) -> None:
        self._uow = uow
        self._receipts = ReceiptRepository(uow.session)
        self._payments = PaymentRepository(uow.session)
        self._activity_svc = activity_svc

    def issue(self, dto: IssueRefundDTO, commit: bool = True) -> RefundResultDTO:
        """
        Issue a refund for an original payment.
        
        Creates a new receipt with a refund line. Validates that refund
        amount doesn't exceed the available amount on the original payment.
        
        For competition payments, also unmarks the team member fee_paid status.
        """
        if dto.amount <= 0:
            raise BusinessRuleError("Refund amount must be positive.")

        # Get original payment
        original = self._payments.get_by_id(dto.payment_id)
        if not original:
            raise NotFoundError(f"Original payment {dto.payment_id} not found.")

        # Validate refund amount
        original_amount = Decimal(str(original.amount))
        already_refunded = self._payments.get_total_refunded(dto.payment_id)
        available = original_amount - already_refunded

        if dto.amount > available:
            raise BusinessRuleError(
                f"Refund amount ({dto.amount}) exceeds available ({available:.2f}). "
                f"Original: {original_amount:.2f}, already refunded: {already_refunded:.2f}"
            )

        # Determine payer name from original receipt
        payer_name = None
        if original.receipt_id:
            orig_receipt = self._receipts.get_by_id(original.receipt_id)
            if orig_receipt:
                payer_name = orig_receipt.payer_name

        # Create refund receipt
        refund_receipt = self._receipts.create(
            CreateReceiptDTO(
                payer_name=payer_name,
                payment_method=dto.method,
                received_by_user_id=dto.received_by_user_id,
                notes=f"Refund: {dto.reason}",
            )
        )
        self._receipts.set_receipt_number(refund_receipt.id)

        # Add refund line
        refund_payment = self._payments.add_line(
            AddPaymentLineDTO(
                receipt_id=refund_receipt.id,
                student_id=original.student_id,
                enrollment_id=original.enrollment_id,
                amount=dto.amount,
                transaction_type="refund",
                team_member_id=original.team_member_id,
                payment_type=original.payment_type,
                notes=dto.reason,
                original_payment_id=dto.payment_id,
            )
        )

        # Handle competition fee unmarking
        if original.payment_type == "competition":
            self._unlink_competition_payment(dto.payment_id, dto.amount)

        # Get updated balance if applicable
        new_balance: Optional[Decimal] = None
        if original.enrollment_id:
            balance_dto = self._payments.get_enrollment_balance(
                original.enrollment_id
            )
            if balance_dto:
                new_balance = balance_dto.balance

        # Log refund activity
        if self._activity_svc and original.student_id:
            self._activity_svc.log_payment(
                LogPaymentDTO(
                    student_id=original.student_id,
                    payment_id=refund_payment.id,
                    amount=Decimal(str(dto.amount)),
                    payment_type="refund",
                    performed_by=dto.received_by_user_id,
                )
            )

        if commit:
            self._uow.commit()
        else:
            self._uow.flush()

        return RefundResultDTO(
            receipt_number=refund_receipt.receipt_number or "",
            refunded_amount=dto.amount,
            new_balance=new_balance,
        )

    def _unlink_competition_payment(
        self, original_payment_id: int, refunded_amount: Decimal
    ) -> None:
        """Internal: Decrement competition fee amount_paid when refunding."""

        stmt = select(Payment).where(Payment.id == original_payment_id)
        payment = self._uow.session.exec(stmt).first()

        if payment and payment.team_member_id:
            # Imported here, not at module level: competitions' model package
            # registers finance's models on import (circular otherwise).
            from app.modules.competitions.models.team_models import TeamMember

            member = self._uow.session.get(TeamMember, payment.team_member_id)
            if member:
                member.amount_paid = max(
                    0.0, float(member.amount_paid) - float(refunded_amount)
                )
                self._uow.session.add(member)
