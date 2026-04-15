"""
app/modules/finance/services/refund_service.py
───────────────────────────────────────────
Refund service implementation with atomic transaction handling.
"""
from decimal import Decimal
from typing import Optional

from app.modules.finance.interfaces import (
    IRefundService,
    RefundResultDTO,
    IssueRefundDTO,
)
from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
from app.shared.exceptions import NotFoundError, BusinessRuleError


class RefundService(IRefundService):
    """
    Service for refund business operations.
    
    Responsible for:
    - Processing refunds against original payments
    - Validating refund amounts don't exceed original
    - Atomic receipt creation with refund line
    - Competition fee unmarking (if applicable)
    """

    def __init__(self, uow: FinanceUnitOfWork) -> None:
        self._uow = uow

    def issue(self, dto: IssueRefundDTO) -> RefundResultDTO:
        """
        Issue a refund for an original payment.
        
        Creates a new receipt with a refund line. Validates that refund
        amount doesn't exceed the available amount on the original payment.
        
        For competition payments, also unmarks the team member fee_paid status.
        """
        if dto.amount <= 0:
            raise BusinessRuleError("Refund amount must be positive.")

        # Get original payment
        original = self._uow.payments.get_by_id(dto.payment_id)
        if not original:
            raise NotFoundError(f"Original payment {dto.payment_id} not found.")

        # Validate refund amount
        original_amount = Decimal(str(original.amount))
        already_refunded = self._uow.payments.get_total_refunded(dto.payment_id)
        available = original_amount - already_refunded

        if dto.amount > available:
            raise BusinessRuleError(
                f"Refund amount ({dto.amount}) exceeds available ({available:.2f}). "
                f"Original: {original_amount:.2f}, already refunded: {already_refunded:.2f}"
            )

        # Determine payer name from original receipt
        payer_name = None
        if original.receipt_id:
            orig_receipt = self._uow.receipts.get_by_id(original.receipt_id)
            if orig_receipt:
                payer_name = orig_receipt.payer_name

        # Create refund receipt
        from app.modules.finance.interfaces import CreateReceiptDTO
        refund_receipt = self._uow.receipts.create(
            CreateReceiptDTO(
                payer_name=payer_name,
                payment_method=dto.method,
                received_by_user_id=dto.received_by_user_id,
                notes=f"Refund: {dto.reason}",
            )
        )
        self._uow.receipts.set_receipt_number(refund_receipt.id)

        # Add refund line
        refund_payment = self._uow.payments.add_line(
            receipt_id=refund_receipt.id,
            student_id=original.student_id,
            enrollment_id=original.enrollment_id,
            amount=amount,
            transaction_type="refund",
            payment_type=original.payment_type,
            notes=reason,
            original_payment_id=payment_id,
        )

        # Handle competition fee unmarking
        if original.payment_type == "competition":
            self._unlink_competition_payment(payment_id)

        # Get updated balance if applicable
        new_balance: Optional[Decimal] = None
        if original.enrollment_id:
            balance_dto = self._uow.payments.get_enrollment_balance(
                original.enrollment_id
            )
            if balance_dto:
                new_balance = balance_dto.balance

        self._uow.commit()

        return RefundResultDTO(
            receipt_number=refund_receipt.receipt_number or "",
            refunded_amount=amount,
            new_balance=new_balance,
        )

    def _unlink_competition_payment(self, original_payment_id: int) -> None:
        """Internal: Unmark competition fees when refunding."""
        from app.modules.competitions.models.team_models import TeamMember
        from sqlalchemy import select

        stmt = select(TeamMember).where(TeamMember.payment_id == original_payment_id)
        members = self._uow._session.exec(stmt).all()

        for member in members:
            member.fee_paid = False
            member.payment_id = None
            self._uow._session.add(member)
