"""
app/modules/academics/repositories/group_details_repository.py
──────────────────────────────────────────────────────────────
Academics-owned data access for the Group Details endpoints.

Reads Finance/Enrollments/Attendance *models* (ADR-0004) instead of reaching
into those modules' repositories, so academics stays self-contained. Query
logic is copied verbatim from the former foreign repositories to keep HTTP
responses byte-identical (including the pinned quirks).
"""
from sqlmodel import Session, select

from app.modules.academics.models.session_models import CourseSession
from app.modules.academics.schemas.group_details_schemas import (
    GroupEnrollmentDTO,
    GroupPaymentRowDTO,
    GroupRosterEntryDTO,
)
from app.modules.attendance.models.attendance_models import Attendance
from sqlalchemy import text


class GroupDetailsRepository:
    """Repository for Group Details reads. Session injected; never commits."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_payments_by_group_with_levels(
        self, group_id: int
    ) -> list[GroupPaymentRowDTO]:
        """All payments for a group, joined through enrollments for the level."""
        stmt = text("""
            SELECT 
                p.id AS payment_id,
                p.receipt_id,
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
            result.append(GroupPaymentRowDTO(
                payment_id=mapping["payment_id"],
                student_id=mapping["student_id"],
                student_name=mapping["student_name"],
                enrollment_id=mapping["enrollment_id"],
                level_number=mapping["level_number"],
                amount=float(mapping["amount"] or 0),
                discount_amount=float(mapping["discount_amount"] or 0),
                payment_date=mapping["payment_date"],
                payment_method=mapping["payment_method"] or "unknown",
                status=mapping["status"],
                receipt_number=mapping["receipt_number"],
                transaction_type=mapping["transaction_type"],
                course_name=mapping["course_name"],
                amount_due=float(mapping["amount_due"] or 0),
                discount_applied=float(mapping["discount_applied"] or 0),
            ))

        return result

    def get_roster_for_group_level(
        self, group_id: int, level_number: int
    ) -> list[GroupRosterEntryDTO]:
        """Active enrollments for a group level with billing status."""
        stmt = text("""
            SELECT 
                e.id AS enrollment_id,
                s.id AS student_id,
                s.full_name AS student_name,
                e.amount_due,
                COALESCE(e.discount_applied, 0) AS discount_applied,
                COALESCE(p.total_paid, 0) AS total_paid,
                (e.amount_due - COALESCE(e.discount_applied, 0) - COALESCE(p.total_paid, 0)) AS balance,
                e.enrolled_at
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            LEFT JOIN (
                SELECT enrollment_id, SUM(amount) as total_paid
                FROM payments
                WHERE deleted_at IS NULL
                GROUP BY enrollment_id
            ) p ON e.id = p.enrollment_id
            WHERE e.group_id = :group_id
                AND e.level_number = :level_number
                AND e.status IN ('active', 'completed')
            ORDER BY s.full_name
        """)

        rows = self._session.execute(
            stmt,
            {"group_id": group_id, "level_number": level_number}
        ).all()

        result = []
        for row in rows:
            mapping = row._mapping
            balance = float(mapping['balance'])
            result.append(GroupRosterEntryDTO(
                enrollment_id=mapping['enrollment_id'],
                student_id=mapping['student_id'],
                student_name=mapping['student_name'],
                billing_status='due' if balance > 0 else 'paid',
                balance=balance,
                joined_at=mapping['enrolled_at'],
            ))

        return result

    def get_enrollments_by_group_with_students(
        self, group_id: int
    ) -> list[GroupEnrollmentDTO]:
        """All enrollments for a group with student, parent and payment detail."""
        stmt = text("""
            SELECT 
                e.id AS enrollment_id,
                e.student_id,
                s.full_name AS student_name,
                s.phone AS student_phone,
                p.full_name AS parent_name,
                e.level_number,
                e.status,
                e.enrolled_at,
                e.amount_due,
                e.discount_applied,
                COALESCE(pay.total_paid, 0) AS amount_paid,
                COALESCE(att.sessions_attended, 0) AS sessions_attended,
                COALESCE(sess.sessions_total, 0) AS sessions_total
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            LEFT JOIN (
                SELECT sp.student_id, par.full_name
                FROM student_parents sp
                JOIN parents par ON sp.parent_id = par.id
                WHERE sp.is_primary = TRUE
            ) p ON e.student_id = p.student_id
            LEFT JOIN (
                SELECT enrollment_id, SUM(amount) AS total_paid
                FROM payments
                WHERE deleted_at IS NULL
                GROUP BY enrollment_id
            ) pay ON e.id = pay.enrollment_id
            LEFT JOIN (
                SELECT a.enrollment_id, COUNT(*) AS sessions_attended
                FROM attendance a
                WHERE a.status IN ('present', 'late')
                GROUP BY a.enrollment_id
            ) att ON e.id = att.enrollment_id
            LEFT JOIN (
                SELECT enrollment_id, COUNT(*) AS sessions_total
                FROM attendance
                GROUP BY enrollment_id
            ) sess ON e.id = sess.enrollment_id
            WHERE e.group_id = :group_id
            ORDER BY e.level_number, s.full_name
        """)

        rows = self._session.execute(stmt, {"group_id": group_id}).all()

        result = []
        for row in rows:
            mapping = row._mapping
            amount_due = float(mapping["amount_due"] or 0)
            discount = float(mapping["discount_applied"] or 0)
            amount_paid = float(mapping["amount_paid"] or 0)
            balance = (amount_due - discount) - amount_paid

            if balance <= 0:
                payment_status = "paid"
            elif amount_paid > 0:
                payment_status = "partial"
            else:
                payment_status = "due"

            can_transfer = mapping["status"] == "active"
            can_drop = mapping["status"] == "active"

            result.append(GroupEnrollmentDTO(
                enrollment_id=mapping["enrollment_id"],
                student_id=mapping["student_id"],
                student_name=mapping["student_name"],
                student_phone=mapping["student_phone"],
                parent_name=mapping["parent_name"],
                level_number=mapping["level_number"],
                status=mapping["status"],
                enrolled_at=mapping["enrolled_at"],
                sessions_attended=mapping["sessions_attended"],
                sessions_total=mapping["sessions_total"],
                payment_status=payment_status,
                amount_due=amount_due,
                amount_paid=amount_paid,
                discount_applied=discount,
                can_transfer=can_transfer,
                can_drop=can_drop,
            ))

        return result

    def get_attendance_for_group_level(
        self, group_id: int, level_number: int
    ) -> list[Attendance]:
        """All attendance records for a specific group level."""
        stmt = (
            select(Attendance)
            .join(CourseSession, Attendance.session_id == CourseSession.id)
            .where(CourseSession.group_id == group_id)
            .where(CourseSession.level_number == level_number)
        )
        return self._session.exec(stmt).all()
