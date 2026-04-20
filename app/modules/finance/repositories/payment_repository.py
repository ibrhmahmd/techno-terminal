"""
app/modules/finance/repositories/payment_repository.py
───────────────────────────────────────────────────
Concrete implementation of payment repository.
"""
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import text
from sqlmodel import Session

from app.modules.finance import Payment
from app.modules.finance.interfaces import (
    IPaymentRepository,
    EnrollmentBalanceDTO,
    AddPaymentLineDTO,
)
from app.modules.finance import EnrollmentBalanceItem
from app.shared.datetime_utils import utc_now


class PaymentRepository(IPaymentRepository):
    """Repository for payment data access operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_line(self, dto: AddPaymentLineDTO) -> Payment:
        """Add a payment line to a receipt."""
        payment = Payment(
            receipt_id=dto.receipt_id,
            student_id=dto.student_id,
            enrollment_id=dto.enrollment_id,
            amount=float(dto.amount),
            transaction_type=dto.transaction_type,
            payment_type=dto.payment_type or "course_level",
            discount_amount=float(dto.discount) if dto.discount else None,
            notes=dto.notes,
            original_payment_id=dto.original_payment_id,
            created_at=utc_now(),
        )
        self._session.add(payment)
        self._session.flush()
        return payment

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        return self._session.get(Payment, payment_id)

    def get_total_refunded(self, original_payment_id: int) -> Decimal:
        """Get total amount refunded for a specific payment."""
        stmt = text("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE original_payment_id = :pid
            AND transaction_type = 'refund'
        """)
        result = self._session.execute(stmt, {"pid": original_payment_id}).scalar()
        return Decimal(str(result or 0))

    def get_enrollment_balance(
        self, enrollment_id: int
    ) -> Optional[EnrollmentBalanceDTO]:
        """Get balance data from v_enrollment_balance view."""
        stmt = text("""
            SELECT 
                enrollment_id,
                student_id,
                group_id,
                level_number,
                amount_due,
                discount_applied,
                total_paid as amount_paid,
                balance,
                payment_status as status
            FROM v_enrollment_balance
            WHERE enrollment_id = :eid
        """)
        row = self._session.execute(stmt, {"eid": enrollment_id}).first()

        if not row:
            return None

        return EnrollmentBalanceDTO(
            enrollment_id=row.enrollment_id,
            student_id=row.student_id,
            group_id=row.group_id,
            level_number=row.level_number,
            amount_due=Decimal(str(row.amount_due or 0)),
            discount_applied=Decimal(str(row.discount_applied or 0)),
            amount_paid=Decimal(str(row.amount_paid or 0)),
            total_refunded=Decimal("0"),  # Not yet implemented in view
            balance=Decimal(str(row.balance or 0)),
            status=row.status or "unknown",
        )

    def get_student_balances(
        self, student_id: int
    ) -> List[EnrollmentBalanceItem]:
        """Get all enrollment balances for a student."""
        stmt = text("""
            SELECT 
                enrollment_id,
                student_id,
                group_id,
                level_number,
                amount_due,
                discount_applied,
                total_paid as amount_paid,
                balance as remaining_balance,
                payment_status as status
            FROM v_enrollment_balance
            WHERE student_id = :sid
            ORDER BY enrollment_id DESC
        """)
        rows = self._session.execute(stmt, {"sid": student_id}).all()

        return [
            EnrollmentBalanceItem(
                enrollment_id=row.enrollment_id,
                student_id=row.student_id,
                group_id=row.group_id,
                level_number=row.level_number,
                amount_due=float(row.amount_due or 0),
                discount_applied=float(row.discount_applied or 0),
                amount_paid=float(row.amount_paid or 0),
                remaining_balance=float(row.remaining_balance or 0),
                status=row.status or "unknown",
            )
            for row in rows
        ]

    def get_unpaid_enrollments(
        self,
        group_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[EnrollmentBalanceItem], int]:
        """
        Get unpaid enrollment balances (where balance < 0).
        Returns items and total count for pagination.
        """
        # Build base query
        base_where = "balance < 0"
        params = {}
        
        if group_id:
            base_where += " AND group_id = :gid"
            params["gid"] = group_id
        
        # Get total count
        count_stmt = text(f"""
            SELECT COUNT(*)
            FROM v_enrollment_balance
            WHERE {base_where}
        """)
        total = self._session.execute(count_stmt, params).scalar() or 0
        
        # Get paginated results
        query_params = {**params, "skip": skip, "limit": limit}
        stmt = text(f"""
            SELECT 
                enrollment_id,
                student_id,
                group_id,
                level_number,
                amount_due,
                discount_applied,
                total_paid as amount_paid,
                balance as remaining_balance,
                payment_status as status
            FROM v_enrollment_balance
            WHERE {base_where}
            ORDER BY balance ASC, enrollment_id DESC
            LIMIT :limit OFFSET :skip
        """)
        rows = self._session.execute(stmt, query_params).all()
        
        items = [
            EnrollmentBalanceItem(
                enrollment_id=row.enrollment_id,
                student_id=row.student_id,
                group_id=row.group_id,
                level_number=row.level_number,
                amount_due=float(row.amount_due or 0),
                discount_applied=float(row.discount_applied or 0),
                amount_paid=float(row.amount_paid or 0),
                remaining_balance=float(row.remaining_balance or 0),
                status=row.status or "unknown",
            )
            for row in rows
        ]
        
        return items, total
