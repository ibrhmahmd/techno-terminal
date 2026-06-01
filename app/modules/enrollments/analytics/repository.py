from datetime import datetime
from sqlalchemy import text
from sqlmodel import Session
from app.modules.enrollments.analytics.schemas import (
    GroupRosterEntryDTO,
    GroupEnrollmentDTO,
)


def get_roster_for_group_level(
    session: Session, group_id: int, level_number: int
) -> list[GroupRosterEntryDTO]:
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

    rows = session.execute(
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
    session: Session, group_id: int
) -> list[GroupEnrollmentDTO]:
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

    rows = session.execute(stmt, {"group_id": group_id}).all()

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
