"""
app/modules/finance/services/receipt_service.py
─────────────────────────────────────────────
Receipt service implementation with proper SOLID compliance.
"""

from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.modules.crm import StudentActivityService

from app.modules.finance.schemas import (
    ReceiptFinalizedDTO,
    ReceiptDetailDTO,
    ReceiptLineItemDTO,
    CreateReceiptServiceDTO,
    SearchReceiptsDTO,
    EnhancedReceiptLineDTO,
)
from app.modules.finance.schemas import ReceiptSearchItem
from app.db.uow import UnitOfWork
from app.modules.crm import LogPaymentDTO
from app.modules.finance.repositories.receipt_repository import ReceiptRepository
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.modules.finance.ports import PaymentNotifier
from app.modules.finance.pdf.receipt_pdf import build_receipt_pdf
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.finance.schemas import CreateReceiptDTO
from app.modules.finance.schemas import AddPaymentLineDTO
from app.modules.crm.models.student_models import Student
from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.course_models import Course
from sqlmodel import select
from app.modules.finance.services.balance_service import BalanceService

logger = logging.getLogger(__name__)


class ReceiptService:
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
        uow: UnitOfWork,
        activity_svc: Optional["StudentActivityService"] = None,
        notifier: Optional[PaymentNotifier] = None,
    ) -> None:
        self._uow = uow
        self._receipts = ReceiptRepository(uow.session)
        self._payments = PaymentRepository(uow.session)
        self._activity_svc = activity_svc
        self._notifier = notifier

    def _require_line_references(self, lines) -> None:
        """404 unless every line's student and enrollment exist (#139).

        The enrollment must belong to the line's student; nothing is written
        when a reference is unknown. (Team-member lines come only from the
        competition fee flow, which has already loaded the member.)
        """
        session = self._uow.session
        for line in lines:
            if session.get(Student, line.student_id) is None:
                raise NotFoundError(f"Student {line.student_id} not found")
            if line.enrollment_id is not None:
                enrollment = session.get(Enrollment, line.enrollment_id)
                if enrollment is None or enrollment.student_id != line.student_id:
                    raise NotFoundError(
                        f"Enrollment {line.enrollment_id} not found for student {line.student_id}"
                    )

    def create(
        self,
        dto: CreateReceiptServiceDTO,
        commit: bool = True,
    ) -> ReceiptFinalizedDTO:
        """
        Create a new receipt with charge lines.

        ``commit=False`` flushes instead of committing, for callers whose own
        use case commits once (e.g. competition fee payment).

        Validates for overpayment risk unless allow_credit=True.
        """
        if not dto.lines:
            raise BusinessRuleError("Receipt must have at least one line item.")
        self._require_line_references(dto.lines)

        # Check overpayment risk if credit not allowed
        if not dto.allow_credit:
            risks = BalanceService(self._uow).assess_overpayment_risk(dto.lines)
            if risks:
                raise BusinessRuleError(
                    f"Overpayment risk detected for {len(risks)} line(s). "
                    "Use allow_credit=true to proceed or adjust amounts."
                )

        # Create receipt and payment lines atomically

        receipt = self._receipts.create(
            CreateReceiptDTO(
                payer_name=dto.payer_name,
                payment_method=dto.payment_method,
                received_by_user_id=dto.received_by_user_id,
                notes=dto.notes,
            )
        )
        self._receipts.set_receipt_number(receipt.id)
        self._uow.flush()

        payment_ids: List[int] = []
        processed_lines: List[ReceiptLineItemDTO] = []

        for line in dto.lines:

            payment = self._payments.add_line(
                AddPaymentLineDTO(
                    receipt_id=receipt.id,
                    student_id=line.student_id,
                    enrollment_id=line.enrollment_id,
                    team_member_id=line.team_member_id,
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

        total = self._receipts.get_total(receipt.id)

        # Log payment activities for each line
        if self._activity_svc:
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

        if commit:
            self._uow.commit()
        else:
            self._uow.flush()

        # Handle Notifications — one notification per receipt (not per line).
        # _process_received already fetches all lines for the receipt, so firing
        # once is correct. Use the first line that has a student_id.
        if self._notifier:
            primary_student_id = next(
                (line.student_id for line in processed_lines if line.student_id), None
            )
            if primary_student_id:
                try:
                    self._notifier.payment_received(
                        receipt_id=receipt.id,
                        student_id=primary_student_id,
                        amount=str(total),
                        receipt_number=str(receipt.receipt_number),
                    )
                except Exception:
                    logger.exception("Payment notifier failed for receipt %s", receipt.id)

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
        data = self._receipts.get_with_lines(receipt_id)
        if not data:
            return None

        total = self._receipts.get_total(receipt_id)

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

        return self._receipts.search(criteria)

    def generate_pdf(self, receipt_id: int) -> bytes:
        """Generate PDF bytes for a receipt with enriched data."""
        data = self._receipts.get_with_lines(receipt_id)
        if not data:
            raise NotFoundError(f"Receipt {receipt_id} not found.")

        total = self._receipts.get_total(receipt_id)

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

        enhanced = []

        for payment in payments:
            # Get student
            student = self._uow.session.get(Student, payment.student_id)
            student_name = (
                student.full_name if student else f"Student #{payment.student_id}"
            )
            student_phone = getattr(student, "phone", None)

            # Get parent info (preferred contact)
            parent_id = None
            parent_name = None
            parent_phone = None
            if student:

                stmt = select(StudentParent).where(
                    StudentParent.student_id == student.id
                )
                parent_link = self._uow.session.exec(stmt).first()
                if parent_link:
                    parent = self._uow.session.get(Parent, parent_link.parent_id)
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
                enrollment = self._uow.session.get(Enrollment, enrollment_id)
                if enrollment:
                    enrollment_status = enrollment.status
                    level_number = enrollment.level_number
                    group_id = enrollment.group_id

                    if group_id:
                        group = self._uow.session.get(Group, group_id)
                        if group:
                            group_name = group.name
                            if group.course_id:
                                course = self._uow.session.get(Course, group.course_id)
                                if course:
                                    course_name = course.name

            # Get balance status for partial payment detection
            is_partial = False
            remaining_amount = 0.0
            balance_status = "unknown"

            if enrollment_id:
                balance_dto = self._payments.get_enrollment_balance(enrollment_id)
                if balance_dto and hasattr(balance_dto, "status"):
                    balance_status = balance_dto.status
                    is_partial = balance_status in ("partial", "unpaid")
                    if (
                        hasattr(balance_dto, "remaining_balance")
                        and balance_dto.remaining_balance < 0
                    ):
                        remaining_amount = abs(balance_dto.remaining_balance)

            enhanced.append(
                EnhancedReceiptLineDTO(
                    payment_id=payment.id,
                    amount=float(payment.amount),
                    transaction_type=payment.transaction_type,
                    payment_type=payment.payment_type,
                    discount_amount=float(getattr(payment, "discount_amount", 0.0)),
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

    def _link_competition_payment(self, team_member_id: int, payment_id: int) -> None:
        """Internal: Link payment to team member for competition fees.

        NOTE: The TeamMember model no longer has fee_paid/payment_id fields
        (removed in migration 054). The link is now via payments.team_member_id FK.
        The competition module manages amount_paid via its own record_payment().
        This method is kept as a no-op for backward compatibility.
        """
        pass
