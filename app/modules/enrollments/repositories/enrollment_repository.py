from datetime import date
from typing import Sequence
from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.shared.audit_utils import apply_update_audit


def create_enrollment(session: Session, enrollment: Enrollment) -> Enrollment:
    session.add(enrollment)
    session.flush()
    return enrollment


def get_enrollment(session: Session, enrollment_id: int) -> Enrollment | None:
    return session.get(Enrollment, enrollment_id)


def get_active_enrollment(
    session: Session, student_id: int, group_id: int
) -> Enrollment | None:
    """Returns the active enrollment for a student in a group, or None."""
    stmt = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .where(Enrollment.group_id == group_id)
        .where(Enrollment.status == "active")
    )
    return session.exec(stmt).first()


def list_enrollments(
    session: Session,
    group_id: int | None = None,
    level_number: int | None = None,
    status: str | None = "active",
) -> Sequence[Enrollment]:
    stmt = select(Enrollment)
    if group_id is not None:
        stmt = stmt.where(Enrollment.group_id == group_id)
    if level_number is not None:
        stmt = stmt.where(Enrollment.level_number == level_number)
    if status is not None:
        stmt = stmt.where(Enrollment.status == status)
    return session.exec(stmt).all()


def update_enrollment_status(
    session: Session, enrollment_id: int, status: str
) -> Enrollment | None:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment:
        enrollment.status = status
        apply_update_audit(enrollment)
        session.add(enrollment)
    return enrollment


def update_discount(
    session: Session, enrollment_id: int, discount: float
) -> Enrollment | None:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment:
        enrollment.discount_applied = discount
        apply_update_audit(enrollment)
        session.add(enrollment)
    return enrollment


def get_enrollments_by_student(
    session: Session, student_id: int
) -> list[Enrollment]:
    """Returns all enrollments for a student across all groups and statuses."""
    stmt = select(Enrollment).where(Enrollment.student_id == student_id)
    return list(session.exec(stmt).all())


def get_roster_for_group_level(
    session: Session, group_id: int, level_number: int
) -> list[dict]:
    """
    Get active enrollments with student details and billing status for a group level.
    Used by attendance grid endpoint.
    
    Balance formula: (amount_due - discount_applied) - total_payments
    billing_status: 'due' if balance > 0 else 'paid'
    
    Returns list of dicts with: enrollment_id, student_id, student_name, 
    billing_status, balance, joined_at
    """
    from sqlalchemy import text
    from datetime import datetime
    
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
            AND e.status = 'active'
        ORDER BY s.full_name
    """)
    
    rows = session.execute(
        stmt, 
        {"group_id": group_id, "level_number": level_number}
    ).all()
    
    result = []
    for row in rows:
        mapping = row._mapping
        balance = float(mapping['balance'])
        result.append({
            "enrollment_id": mapping['enrollment_id'],
            "student_id": mapping['student_id'],
            "student_name": mapping['student_name'],
            "billing_status": 'due' if balance > 0 else 'paid',
            "balance": balance,
            "joined_at": mapping['enrolled_at'],
        })
    
    return result
