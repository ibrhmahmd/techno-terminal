"""
app/modules/finance/services/receipt_service.py
─────────────────────────────────────────────
Receipt service implementation with proper SOLID compliance.
"""
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from fastapi import BackgroundTasks

if TYPE_CHECKING:
    from app.modules.crm.services.activity_service import StudentActivityService
    from app.modules.notifications.services.notification_service import NotificationService

from app.modules.finance.interfaces import (
    IReceiptService,
    ReceiptFinalizedDTO,
    ReceiptDetailDTO,
    ReceiptLineItemDTO,
    CreateReceiptServiceDTO,
    SearchReceiptsDTO,
    EnhancedReceiptLineDTO,
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

    def __init__(
        self,
        uow: FinanceUnitOfWork,
        activity_svc: Optional["StudentActivityService"] = None,
        notification_svc: Optional["NotificationService"] = None,
    ) -> None:
        self._uow = uow
        self._activity_svc = activity_svc
        self._notification_svc = notification_svc

    def create(self, dto: CreateReceiptServiceDTO, background_tasks: Optional[BackgroundTasks] = None) -> ReceiptFinalizedDTO:
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

        # Log payment activities for each line
        if self._activity_svc:
            from app.modules.crm.interfaces.dtos.log_payment_dto import LogPaymentDTO
            for line in processed_lines:
                if line.student_id:  # Only log if associated with a student
                    self._activity_svc.log_payment(
                        LogPaymentDTO(
                            student_id=line.student_id,
                            payment_id=line.id,
                            amount=line.amount,
                            payment_type=line.payment_type or "course_level",
                            performed_by=dto.received_by_user_id,
                        )
                    )

        # Handle Notifications
        if self._notification_svc and background_tasks:
            for line in processed_lines:
                if line.student_id:
                    self._notification_svc.notify_payment_receipt(
                        receipt.id, line.student_id, str(line.amount), str(receipt.receipt_number), background_tasks
                    )

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
        """Generate PDF bytes for a receipt with enriched data."""
        data = self._uow.receipts.get_with_lines(receipt_id)
        if not data:
            raise NotFoundError(f"Receipt {receipt_id} not found.")

        total = self._uow.receipts.get_total(receipt_id)

        # Build enriched lines with full student, enrollment, and balance data
        enhanced_lines = self._build_enhanced_lines(data.lines)

        # Get payer info from first line
        payer_name = data.receipt.payer_name or "N/A"
        payer_phone = None
        if enhanced_lines:
            payer_phone = enhanced_lines[0].display_phone
            if not data.receipt.payer_name:
                payer_name = enhanced_lines[0].display_contact_name

        return build_receipt_pdf(
            receipt=data.receipt,
            lines=enhanced_lines,
            total=float(total),
            payer_name=payer_name,
            payer_phone=payer_phone,
            currency="EGP",
        )

    def _build_enhanced_lines(self, payments) -> List[EnhancedReceiptLineDTO]:
        """
        Build enriched receipt line DTOs with student, enrollment, group, and balance data.
        """
        from app.modules.crm.models.student_models import Student
        from app.modules.crm.models.parent_models import Parent
        from app.modules.crm.models.link_models import StudentParent
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models.group_models import Group
        from app.modules.academics.models.course_models import Course

        enhanced = []

        for payment in payments:
            # Get student
            student = self._uow.get_model_by_id(Student, payment.student_id)
            student_name = student.full_name if student else f"Student #{payment.student_id}"
            student_phone = getattr(student, 'phone', None)

            # Get parent info (preferred contact)
            parent_id = None
            parent_name = None
            parent_phone = None
            if student:
                from sqlmodel import select
                stmt = select(StudentParent).where(StudentParent.student_id == student.id)
                parent_link = self._uow._session.exec(stmt).first()
                if parent_link:
                    parent = self._uow.get_model_by_id(Parent, parent_link.parent_id)
                    if parent:
                        parent_id = parent.id
                        parent_name = parent.full_name
                        parent_phone = parent.phone_primary or parent.phone_secondary

            # Get enrollment and group info
            enrollment_id = payment.enrollment_id
            enrollment_status = None
            level_number = None
            group_id = None
            group_name = None
            course_name = None

            if enrollment_id:
                enrollment = self._uow.get_model_by_id(Enrollment, enrollment_id)
                if enrollment:
                    enrollment_status = enrollment.status
                    level_number = enrollment.level_number
                    group_id = enrollment.group_id

                    if group_id:
                        group = self._uow.get_model_by_id(Group, group_id)
                        if group:
                            group_name = group.name
                            if group.course_id:
                                course = self._uow.get_model_by_id(Course, group.course_id)
                                if course:
                                    course_name = course.name

            # Get balance status for partial payment detection
            is_partial = False
            remaining_amount = 0.0
            balance_status = "unknown"

            if enrollment_id:
                balance_dto = self._uow.payments.get_enrollment_balance(enrollment_id)
                if balance_dto and hasattr(balance_dto, 'status'):
                    balance_status = balance_dto.status
                    is_partial = balance_status in ('partial', 'unpaid')
                    if hasattr(balance_dto, 'remaining_balance') and balance_dto.remaining_balance < 0:
                        remaining_amount = abs(balance_dto.remaining_balance)

            enhanced.append(
                EnhancedReceiptLineDTO(
                    payment_id=payment.id,
                    amount=float(payment.amount),
                    transaction_type=payment.transaction_type,
                    payment_type=payment.payment_type,
                    discount_amount=float(getattr(payment, 'discount_amount', 0.0)),
                    notes=payment.notes,
                    student_id=payment.student_id,
                    student_name=student_name,
                    student_phone=student_phone,
                    parent_id=parent_id,
                    parent_name=parent_name,
                    parent_phone=parent_phone,
                    enrollment_id=enrollment_id,
                    enrollment_status=enrollment_status,
                    level_number=level_number,
                    group_id=group_id,
                    group_name=group_name,
                    course_name=course_name,
                    is_partial_payment=is_partial,
                    remaining_amount=remaining_amount,
                    balance_status=balance_status,
                    payment=payment,
                    student=student,
                    enrollment=enrollment if enrollment_id else None,
                    group=None,  # Not loading ORM to avoid lazy loading issues
                    parent=None,  # Not loading ORM to avoid lazy loading issues
                )
            )

        return enhanced

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
