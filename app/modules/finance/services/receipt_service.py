"""
app/modules/finance/services/receipt_service.py
─────────────────────────────────────────────
Receipt service implementation with proper SOLID compliance.
"""
from decimal import Decimal
from typing import Optional, List

from app.modules.finance.interfaces import (
    IReceiptService,
    ReceiptFinalizedDTO,
    ReceiptDetailDTO,
    ReceiptLineItemDTO,
    CreateReceiptServiceDTO,
    SearchReceiptsDTO,
)
from app.modules.finance import ReceiptSearchItem, ReceiptLineInput
from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
from app.modules.finance.pdf.receipt_pdf import build_receipt_pdf
from app.shared.exceptions import NotFoundError, BusinessRuleError


class ReceiptService(IReceiptService):
    """
    Service for receipt business operations.
    
    Responsible for:
    - Receipt creation with charge lines
    - Receipt retrieval and search
    - PDF generation
    - Receipt finalization
    """

    def __init__(self, uow: FinanceUnitOfWork) -> None:
        self._uow = uow

    def create(self, dto: CreateReceiptServiceDTO) -> ReceiptFinalizedDTO:
        """
        Create a new receipt with charge lines.
        
        Validates for overpayment risk unless allow_credit=True.
        """
        if not dto.lines:
            raise BusinessRuleError("Receipt must have at least one line item.")

        # Check overpayment risk if credit not allowed
        if not dto.allow_credit:
            risks = self._assess_overpayment_risk(dto.lines)
            if risks:
                raise BusinessRuleError(
                    f"Overpayment risk detected for {len(risks)} line(s). "
                    "Use allow_credit=true to proceed or adjust amounts."
                )

        # Create receipt and payment lines atomically
        from app.modules.finance.interfaces import CreateReceiptDTO
        receipt = self._uow.receipts.create(
            CreateReceiptDTO(
                payer_name=dto.payer_name,
                payment_method=dto.payment_method,
                received_by_user_id=dto.received_by_user_id,
                notes=dto.notes,
            )
        )
        self._uow.receipts.set_receipt_number(receipt.id)
        self._uow.flush()

        payment_ids: List[int] = []
        processed_lines: List[ReceiptLineItemDTO] = []

        for line in dto.lines:
            from app.modules.finance.interfaces import AddPaymentLineDTO
            payment = self._uow.payments.add_line(
                AddPaymentLineDTO(
                    receipt_id=receipt.id,
                    student_id=line.student_id,
                    enrollment_id=line.enrollment_id,
                    amount=Decimal(str(line.amount)),
                    transaction_type="payment",
                    payment_type=line.payment_type or "course_level",
                    discount=Decimal(str(line.discount or 0)),
                    notes=line.notes,
                )
            )
            payment_ids.append(payment.id)

            # Handle competition payment linking
            if line.payment_type == "competition" and line.team_member_id:
                self._link_competition_payment(line.team_member_id, payment.id)

            processed_lines.append(
                ReceiptLineItemDTO(
                    id=payment.id,
                    student_id=payment.student_id,
                    enrollment_id=payment.enrollment_id,
                    amount=Decimal(str(payment.amount)),
                    transaction_type=payment.transaction_type,
                    payment_type=payment.payment_type or "course_level",
                    discount=Decimal(str(payment.discount_amount or 0)),
                    notes=payment.notes,
                )
            )

        total = self._uow.receipts.get_total(receipt.id)
        self._uow.commit()

        return ReceiptFinalizedDTO(
            receipt_id=receipt.id,
            receipt_number=receipt.receipt_number or "",
            payment_method=receipt.payment_method,
            paid_at=receipt.paid_at,
            lines=processed_lines,
            total=total,
            payment_ids=payment_ids,
        )

    def get_detail(self, receipt_id: int) -> Optional[ReceiptDetailDTO]:
        """Get detailed receipt information with line items."""
        data = self._uow.receipts.get_with_lines(receipt_id)
        if not data:
            return None

        total = self._uow.receipts.get_total(receipt_id)

        line_dtos = [
            ReceiptLineItemDTO(
                id=line.id,
                student_id=line.student_id,
                enrollment_id=line.enrollment_id,
                amount=Decimal(str(line.amount)),
                transaction_type=line.transaction_type,
                payment_type=line.payment_type or "course_level",
                discount=Decimal(str(line.discount_amount or 0)),
                notes=line.notes,
            )
            for line in data.lines
        ]

        return ReceiptDetailDTO(
            receipt=data.receipt,
            lines=line_dtos,
            total=total,
        )

    def search(self, criteria: SearchReceiptsDTO) -> List[ReceiptSearchItem]:
        """Search receipts with date range and optional filters."""
        if criteria.to_date < criteria.from_date:
            raise BusinessRuleError("End date must be on or after start date.")

        return self._uow.receipts.search(criteria)

    def generate_pdf(self, receipt_id: int) -> bytes:
        """Generate PDF bytes for a receipt."""
        data = self._uow.receipts.get_with_lines(receipt_id)
        if not data:
            raise NotFoundError(f"Receipt {receipt_id} not found.")

        total = self._uow.receipts.get_total(receipt_id)

        # Get parent name from first student
        parent_name = "N/A"
        if data.lines:
            from app.modules.crm.models import Student
            student = self._uow._session.get(Student, data.lines[0].student_id)
            if student and student.parent_links:
                primary_link = next(
                    (link for link in student.parent_links if link.is_primary),
                    student.parent_links[0] if student.parent_links else None
                )
                if primary_link and primary_link.parent:
                    parent_name = primary_link.parent.full_name

        return build_receipt_pdf(
            receipt=data.receipt,
            lines=data.lines,
            total=float(total),
            parent_name=parent_name,
        )

    def mark_as_sent(self, receipt_id: int) -> None:
        """Mark a receipt as sent (notification status)."""
        # TODO: Implement when notification tracking is added
        pass

    def _assess_overpayment_risk(
        self, lines: List[ReceiptLineInput]
    ) -> List:
        """Internal: Check which lines would create credit."""
        from app.modules.finance.interfaces import OverpaymentRiskItem

        risks = []
        for line in lines:
            if not line.enrollment_id:
                continue

            balance_dto = self._uow.payments.get_enrollment_balance(line.enrollment_id)
            if not balance_dto:
                continue

            current_balance = balance_dto.balance
            pay_amount = Decimal(str(line.amount))
            projected_balance = current_balance + pay_amount

            if projected_balance > 0:
                debt_before = max(-current_balance, Decimal("0"))
                risks.append(
                    OverpaymentRiskItem(
                        student_id=line.student_id,
                        enrollment_id=line.enrollment_id,
                        amount=pay_amount,
                        debt_before=debt_before,
                        projected_balance=projected_balance,
                        excess_credit=max(pay_amount - debt_before, Decimal("0")),
                    )
                )

        return risks

    def _link_competition_payment(
        self, team_member_id: int, payment_id: int
    ) -> None:
        """Internal: Link payment to team member for competition fees."""
        from app.modules.competitions.models.team_models import TeamMember

        team_member = self._uow._session.get(TeamMember, team_member_id)
        if team_member:
            team_member.fee_paid = True
            team_member.payment_id = payment_id
            self._uow._session.add(team_member)
