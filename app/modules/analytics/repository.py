"""
analytics/repository.py — Raw SQL queries for reporting.
All functions accept a Session and return list[dict] or dict.
"""

from datetime import date
from typing import Optional
from sqlmodel import Session
from sqlalchemy import text


# ── Today's Operations ────────────────────────────────────────────────────────


def get_today_sessions(db: Session, target_date: Optional[date] = None) -> list[dict]:
    """All sessions on a given date with group, course, instructor, and attendance counts."""
    if target_date is None:
        target_date = date.today()
    stmt = text("""
        SELECT
            s.id AS session_id,
            s.session_date,
            s.start_time,
            s.end_time,
            s.session_number,
            s.level_number,
            g.id AS group_id,
            c.name AS course_name,
            g.name AS group_name,
            COALESCE(e.full_name, 'Unassigned') AS instructor_name,
            COUNT(a.id) FILTER (WHERE a.status IN ('present', 'late')) AS present,
            COUNT(a.id) FILTER (WHERE a.status = 'absent') AS absent,
            COUNT(a.id) FILTER (WHERE a.status IS NULL OR a.status = 'unmarked') AS unmarked,
            COUNT(en.id) AS total_enrolled
        FROM sessions s
        JOIN groups g ON s.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON COALESCE(s.actual_instructor_id, g.instructor_id) = e.id
        LEFT JOIN attendance a ON a.session_id = s.id
        LEFT JOIN enrollments en ON en.group_id = g.id
            AND en.level_number = s.level_number
            AND en.status = 'active'
        WHERE s.session_date = :target_date
        GROUP BY s.id, g.id, c.name, g.name, e.full_name
        ORDER BY s.start_time
    """)
    rows = db.execute(stmt, {"target_date": str(target_date)}).all()
    return [dict(r._mapping) for r in rows]


def get_today_unpaid_attendees(
    db: Session, target_date: Optional[date] = None
) -> list[dict]:
    """Students who attended today but have an outstanding balance on any enrollment."""
    if target_date is None:
        target_date = date.today()
    stmt = text("""
        SELECT DISTINCT
            st.id AS student_id,
            st.full_name AS student_name,
            g.full_name AS guardian_name,
            g.phone_primary,
            SUM(vb.balance) OVER (PARTITION BY st.id) AS total_balance
        FROM attendance a
        JOIN sessions s ON a.session_id = s.id
        JOIN students st ON a.student_id = st.id
        JOIN v_enrollment_balance vb ON vb.student_id = st.id
        LEFT JOIN student_guardians sg ON sg.student_id = st.id AND sg.is_primary = TRUE
        LEFT JOIN guardians g ON g.id = sg.guardian_id
        WHERE s.session_date = :target_date
          AND a.status IN ('present', 'late')
          AND vb.balance > 0
        ORDER BY total_balance DESC
    """)
    rows = db.execute(stmt, {"target_date": str(target_date)}).all()
    return [dict(r._mapping) for r in rows]


# ── Financial Reporting ───────────────────────────────────────────────────────


def get_revenue_by_date(db: Session, start: date, end: date) -> list[dict]:
    """Daily revenue totals between two dates."""
    stmt = text("""
        SELECT
            DATE(r.paid_at) AS day,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
              - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS net_revenue
        FROM receipts r
        JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) BETWEEN :start AND :end
        GROUP BY day
        ORDER BY day
    """)
    rows = db.execute(stmt, {"start": str(start), "end": str(end)}).all()
    return [dict(r._mapping) for r in rows]


def get_revenue_by_method(db: Session, start: date, end: date) -> list[dict]:
    """Revenue totals grouped by payment method between two dates."""
    stmt = text("""
        SELECT
            r.payment_method,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
              - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS net_revenue,
            COUNT(DISTINCT r.id) AS receipt_count
        FROM receipts r
        JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) BETWEEN :start AND :end
        GROUP BY r.payment_method
        ORDER BY net_revenue DESC
    """)
    rows = db.execute(stmt, {"start": str(start), "end": str(end)}).all()
    return [dict(r._mapping) for r in rows]


def get_outstanding_by_group(db: Session) -> list[dict]:
    """Sum of unpaid balances per active group."""
    stmt = text("""
        SELECT
            g.id AS group_id,
            g.name AS group_name,
            c.name AS course_name,
            COUNT(DISTINCT vb.student_id) AS students_with_balance,
            SUM(vb.balance) AS total_outstanding
        FROM v_enrollment_balance vb
        JOIN groups g ON vb.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        WHERE vb.balance > 0 AND g.status = 'active'
        GROUP BY g.id, g.name, c.name
        ORDER BY total_outstanding DESC
    """)
    rows = db.execute(stmt).all()
    return [dict(r._mapping) for r in rows]


def get_top_debtors(db: Session, limit: int = 10) -> list[dict]:
    """Students with the highest combined outstanding balances."""
    stmt = text("""
        SELECT
            st.id AS student_id,
            st.full_name AS student_name,
            g.full_name AS guardian_name,
            g.phone_primary,
            SUM(vb.balance) AS total_outstanding
        FROM v_enrollment_balance vb
        JOIN students st ON vb.student_id = st.id
        LEFT JOIN student_guardians sg ON sg.student_id = st.id AND sg.is_primary = TRUE
        LEFT JOIN guardians g ON g.id = sg.guardian_id
        WHERE vb.balance > 0
        GROUP BY st.id, st.full_name, g.full_name, g.phone_primary
        ORDER BY total_outstanding DESC
        LIMIT :limit
    """)
    rows = db.execute(stmt, {"limit": limit}).all()
    return [dict(r._mapping) for r in rows]


# ── Academic Reporting ────────────────────────────────────────────────────────


def get_group_roster(db: Session, group_id: int, level_number: int) -> list[dict]:
    """Students in a group level with attendance % and balance."""
    stmt = text("""
        SELECT
            st.id AS student_id,
            st.full_name AS student_name,
            en.id AS enrollment_id,
            en.status AS enrollment_status,
            COALESCE(vb.balance, 0) AS balance,
            COALESCE(att.sessions_attended, 0) AS sessions_attended,
            COALESCE(att.sessions_missed, 0) AS sessions_missed,
            COALESCE(vgs.total_sessions, 0) AS total_sessions,
            CASE
                WHEN COALESCE(vgs.total_sessions, 0) = 0 THEN 0
                ELSE ROUND(
                    100.0 * COALESCE(att.sessions_attended, 0) / vgs.total_sessions, 1
                )
            END AS attendance_pct
        FROM enrollments en
        JOIN students st ON en.student_id = st.id
        LEFT JOIN v_enrollment_balance vb ON vb.enrollment_id = en.id
        LEFT JOIN v_enrollment_attendance att ON att.enrollment_id = en.id
        LEFT JOIN v_group_session_count vgs ON vgs.group_id = en.group_id
            AND vgs.level_number = en.level_number
        WHERE en.group_id = :group_id AND en.level_number = :level
        ORDER BY st.full_name
    """)
    rows = db.execute(stmt, {"group_id": group_id, "level": level_number}).all()
    return [dict(r._mapping) for r in rows]


def get_attendance_heatmap(db: Session, group_id: int, level_number: int) -> list[dict]:
    """Returns per-student per-session attendance status for a group+level."""
    stmt = text("""
        SELECT
            st.id AS student_id,
            st.full_name AS student_name,
            s.id AS session_id,
            s.session_number,
            s.session_date,
            COALESCE(a.status, 'unmarked') AS status
        FROM enrollments en
        JOIN students st ON en.student_id = st.id
        CROSS JOIN sessions s
        LEFT JOIN attendance a ON a.student_id = st.id AND a.session_id = s.id
        WHERE en.group_id = :group_id
          AND en.level_number = :level
          AND s.group_id = :group_id
          AND s.level_number = :level
        ORDER BY st.full_name, s.session_number
    """)
    rows = db.execute(stmt, {"group_id": group_id, "level": level_number}).all()
    return [dict(r._mapping) for r in rows]


# ── Competitions Reporting ────────────────────────────────────────────────────


def get_competition_fee_summary(db: Session) -> list[dict]:
    """Per-competition: teams, members, fees collected vs owed."""
    stmt = text("""
        SELECT
            cp.id AS competition_id,
            cp.name AS competition_name,
            cp.competition_date,
            COUNT(DISTINCT t.id) AS team_count,
            COUNT(DISTINCT tm.id) AS member_count,
            COALESCE(SUM(t.enrollment_fee_per_student) FILTER (WHERE tm.fee_paid = TRUE), 0) AS fees_collected,
            COALESCE(SUM(t.enrollment_fee_per_student) FILTER (WHERE tm.fee_paid = FALSE
                AND t.enrollment_fee_per_student IS NOT NULL), 0) AS fees_outstanding
        FROM competitions cp
        LEFT JOIN competition_categories cc ON cc.competition_id = cp.id
        LEFT JOIN teams t ON t.category_id = cc.id
        LEFT JOIN team_members tm ON tm.team_id = t.id
        GROUP BY cp.id, cp.name, cp.competition_date
        ORDER BY cp.competition_date DESC NULLS LAST, cp.id DESC
    """)
    rows = db.execute(stmt).all()
    return [dict(r._mapping) for r in rows]
