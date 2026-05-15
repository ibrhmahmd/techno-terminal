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
    PaymentWithDetailsDTO,
    PaymentListItemDTO,
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
        """Get all enrollment balances for a student with group details."""
        stmt = text("""
            SELECT
                vb.enrollment_id,
                vb.student_id,
                s.full_name as student_name,
                vb.group_id,
                g.name as group_name,
                c.name as course_name,
                vb.level_number,
                vb.amount_due,
                vb.discount_applied,
                vb.total_paid as amount_paid,
                vb.balance as remaining_balance,
                vb.payment_status as status,
                e.enrolled_at
            FROM v_enrollment_balance vb
            JOIN students s ON s.id = vb.student_id
            JOIN groups g ON g.id = vb.group_id
            LEFT JOIN courses c ON c.id = g.course_id
            JOIN enrollments e ON e.id = vb.enrollment_id
            WHERE vb.student_id = :sid
              AND e.status = 'active'
            ORDER BY vb.enrollment_id DESC
        """)
        rows = self._session.execute(stmt, {"sid": student_id}).all()

        return [
            EnrollmentBalanceItem(
                enrollment_id=row.enrollment_id,
                student_id=row.student_id,
                student_name=row.student_name or "",
                group_id=row.group_id,
                group_name=row.group_name or "",
                course_name=row.course_name,
                level_number=row.level_number,
                amount_due=float(row.amount_due or 0),
                discount_applied=float(row.discount_applied or 0),
                amount_paid=float(row.amount_paid or 0),
                remaining_balance=float(row.remaining_balance or 0),
                status=row.status or "unknown",
                enrolled_at=str(row.enrolled_at) if row.enrolled_at else None,
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
        Get unpaid enrollment balances from v_unpaid_enrollments view.
        Returns items and total count for pagination.
        """
        # Build base query - v_unpaid_enrollments already filters for unpaid
        base_where = "1=1"
        params = {}

        if group_id:
            base_where += " AND group_id = :gid"
            params["gid"] = group_id

        # Get total count
        count_stmt = text(f"""
            SELECT COUNT(*)
            FROM v_unpaid_enrollments
            WHERE {base_where}
        """)
        total = self._session.execute(count_stmt, params).scalar() or 0

        # Get paginated results
        query_params = {**params, "skip": skip, "limit": limit}
        stmt = text(f"""
            SELECT
                enrollment_id,
                student_id,
                student_name,
                group_id,
                group_name,
                course_name,
                level_number,
                amount_due,
                discount_applied,
                total_paid as amount_paid,
                remaining_balance,
                balance,
                payment_status as status,
                enrolled_at
            FROM v_unpaid_enrollments
            WHERE {base_where}
            ORDER BY remaining_balance ASC, enrollment_id DESC
            LIMIT :limit OFFSET :skip
        """)
        rows = self._session.execute(stmt, query_params).all()

        items = [
            EnrollmentBalanceItem(
                enrollment_id=row.enrollment_id,
                student_id=row.student_id,
                student_name=row.student_name or "",
                group_id=row.group_id,
                group_name=row.group_name or "",
                course_name=row.course_name,
                level_number=row.level_number,
                amount_due=float(row.amount_due or 0),
                discount_applied=float(row.discount_applied or 0),
                amount_paid=float(row.amount_paid or 0),
                remaining_balance=float(row.remaining_balance or 0),
                status=row.status or "unknown",
                enrolled_at=str(row.enrolled_at) if row.enrolled_at else None,
            )
            for row in rows
        ]

        return items, total

    def get_payments_by_student(
        self, student_id: int, skip: int = 0, limit: int = 50
    ) -> tuple[List[PaymentListItemDTO], int]:
        """
        Get paginated payments for a specific student with receipt and course info.
        
        Returns:
            Tuple of (list of PaymentListItemDTO, total count)
        """
        # Build base query with joins for all needed data
        base_where = "p.student_id = :sid AND p.deleted_at IS NULL"
        params = {"sid": student_id}
        
        # Count query
        count_stmt = text(f"""
            SELECT COUNT(*)
            FROM payments p
            WHERE {base_where}
        """)
        total = self._session.execute(count_stmt, params).scalar() or 0
        
        # Data query with joins
        query_params = {**params, "skip": skip, "limit": limit}
        stmt = text(f"""
            SELECT 
                p.id,
                p.student_id,
                p.amount,
                COALESCE(r.paid_at, p.created_at) as payment_date,
                r.payment_method,
                'completed' as status,
                p.receipt_id,
                r.receipt_number,
                c.name as course_name,
                cg.name as group_name,
                p.enrollment_id,
                p.transaction_type,
                e.level_number
            FROM payments p
            LEFT JOIN receipts r ON p.receipt_id = r.id
            LEFT JOIN enrollments e ON p.enrollment_id = e.id
            LEFT JOIN groups cg ON e.group_id = cg.id
            LEFT JOIN courses c ON cg.course_id = c.id
            WHERE {base_where}
            ORDER BY COALESCE(r.paid_at, p.created_at) DESC
            LIMIT :limit OFFSET :skip
        """)
        
        rows = self._session.execute(stmt, query_params).all()
        
        items = [
            PaymentListItemDTO(
                id=row.id,
                student_id=row.student_id,
                amount=Decimal(str(row.amount or 0)),
                payment_date=row.payment_date,
                payment_method=row.payment_method,
                status=row.status,
                receipt_id=row.receipt_id,
                receipt_number=row.receipt_number,
                course_name=row.course_name,
                group_name=row.group_name,
                level_number=row.level_number,
                transaction_type=row.transaction_type or "payment",
            )
            for row in rows
        ]
        
        return items, total

    def get_payment_with_details(
        self, payment_id: int
    ) -> Optional[PaymentWithDetailsDTO]:
        """
        Get detailed payment information with all related data.
        
        Includes:
        - Payment fields
        - Receipt fields
        - Enrollment, group, course info
        - Instructor name
        - Student snapshot
        - Parent contact info
        """
        stmt = text("""
            SELECT 
                -- Payment fields
                p.id as payment_id,
                p.student_id,
                p.amount,
                p.payment_type,
                p.transaction_type,
                COALESCE(p.discount_amount, 0) as discount_amount,
                p.notes as payment_notes,
                p.created_at,
                p.enrollment_id,
                
                -- Receipt fields
                r.id as receipt_id,
                r.receipt_number,
                r.payment_method,
                r.paid_at,
                r.received_by,
                r.notes as receipt_notes,
                u.username as received_by_name,
                
                -- Group/Course fields
                cg.id as group_id,
                cg.name as group_name,
                c.name as course_name,
                e.level_number,
                
                -- Instructor fields
                emp.id as instructor_id,
                emp.full_name as instructor_name,
                
                -- Student fields
                s.full_name as student_name,
                s.phone as student_phone,
                
                -- Parent fields (get primary parent - first one)
                par.id as parent_id,
                par.full_name as parent_name,
                par.phone as parent_phone
                
            FROM payments p
            LEFT JOIN receipts r ON p.receipt_id = r.id
            LEFT JOIN users u ON r.received_by = u.id
            LEFT JOIN enrollments e ON p.enrollment_id = e.id
            LEFT JOIN groups cg ON e.group_id = cg.id
            LEFT JOIN courses c ON cg.course_id = c.id
            LEFT JOIN employees emp ON cg.instructor_id = emp.id
            LEFT JOIN students s ON p.student_id = s.id
            LEFT JOIN LATERAL (
                SELECT parent.id, parent.full_name, parent.phone_primary as phone
                FROM parents parent
                JOIN student_parents sp ON parent.id = sp.parent_id
                WHERE sp.student_id = p.student_id
                ORDER BY sp.is_primary DESC, parent.id
                LIMIT 1
            ) par ON true
            WHERE p.id = :pid AND p.deleted_at IS NULL
        """)
        
        row = self._session.execute(stmt, {"pid": payment_id}).first()
        
        if not row:
            return None
        
        return PaymentWithDetailsDTO(
            # Payment fields
            payment_id=row.payment_id,
            student_id=row.student_id,
            amount=Decimal(str(row.amount or 0)),
            payment_type=row.payment_type,
            transaction_type=row.transaction_type or "payment",
            discount_amount=Decimal(str(row.discount_amount or 0)),
            notes=row.payment_notes,
            created_at=row.created_at,
            
            # Receipt fields
            receipt_id=row.receipt_id,
            receipt_number=row.receipt_number,
            payment_method=row.payment_method,
            paid_at=row.paid_at,
            received_by=row.received_by,
            received_by_name=row.received_by_name,
            receipt_notes=row.receipt_notes,
            
            # Enrollment/Group/Course fields
            enrollment_id=row.enrollment_id,
            group_id=row.group_id,
            group_name=row.group_name,
            course_name=row.course_name,
            level_number=row.level_number,
            
            # Instructor fields
            instructor_id=row.instructor_id,
            instructor_name=row.instructor_name,
            
            # Student fields
            student_name=row.student_name or f"Student #{row.student_id}",
            student_phone=row.student_phone,
            
            # Parent fields
            parent_id=row.parent_id,
            parent_name=row.parent_name,
            parent_phone=row.parent_phone,
        )

    def get_payments_by_group_with_levels(
        self, group_id: int
    ) -> list[dict]:
        """
        Get all payments for a group with level breakdown.
        Joins through enrollments to get level_number.
        
        Returns list of dicts with payment + enrollment data including:
        - payment_id, student_id, student_name
        - enrollment_id, level_number
        - amount, discount, payment_date, payment_method, status
        - receipt_number, transaction_type
        """
        stmt = text("""
            SELECT 
                p.id AS payment_id,
                p.student_id,
                s.full_name AS student_name,
                p.enrollment_id,
                e.level_number,
                p.amount,
                COALESCE(p.discount_amount, 0) AS discount_amount,
                COALESCE(r.paid_at, p.created_at) AS payment_date,
                r.payment_method,
                CASE 
                    WHEN p.transaction_type = 'refund' THEN 'refunded'
                    WHEN p.transaction_type = 'adjustment' THEN 'completed'
                    ELSE 'completed'
                END AS status,
                r.receipt_number,
                p.transaction_type,
                COALESCE(c.name, 'Unknown') AS course_name,
                e.amount_due,
                e.discount_applied
            FROM payments p
            JOIN enrollments e ON p.enrollment_id = e.id
            JOIN students s ON p.student_id = s.id
            LEFT JOIN receipts r ON p.receipt_id = r.id
            LEFT JOIN groups g ON e.group_id = g.id
            LEFT JOIN courses c ON g.course_id = c.id
            WHERE e.group_id = :group_id
                AND p.deleted_at IS NULL
            ORDER BY e.level_number, p.created_at DESC
        """)
        
        rows = self._session.execute(stmt, {"group_id": group_id}).all()
        
        result = []
        for row in rows:
            mapping = row._mapping
            result.append({
                "payment_id": mapping["payment_id"],
                "student_id": mapping["student_id"],
                "student_name": mapping["student_name"],
                "enrollment_id": mapping["enrollment_id"],
                "level_number": mapping["level_number"],
                "amount": float(mapping["amount"] or 0),
                "discount_amount": float(mapping["discount_amount"] or 0),
                "payment_date": mapping["payment_date"],
                "payment_method": mapping["payment_method"] or "unknown",
                "status": mapping["status"],
                "receipt_number": mapping["receipt_number"],
                "transaction_type": mapping["transaction_type"],
                "course_name": mapping["course_name"],
                "amount_due": float(mapping["amount_due"] or 0),
                "discount_applied": float(mapping["discount_applied"] or 0),
            })
        
        return result
