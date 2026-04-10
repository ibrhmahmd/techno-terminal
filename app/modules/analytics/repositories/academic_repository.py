"""
app/modules/analytics/repositories/academic_repository.py
─────────────────────────────────────────────────────────
Data access layer for academic analytics.
"""

from datetime import date
from typing import Optional
from sqlmodel import Session
from sqlalchemy import text
from app.modules.analytics.schemas import (
    TodaySessionDTO,
    UnpaidAttendeeDTO,
    GroupRosterRowDTO,
    AttendanceHeatmapRowDTO,
    StudentProgressDTO,
    CourseCompletionDTO,
)


def get_active_enrollment_count(db: Session) -> int:
    """Total number of active enrollments across all groups and courses."""
    stmt = text("SELECT COUNT(id) FROM enrollments WHERE status = 'active'")
    result = db.execute(stmt).scalar()
    return int(result or 0)


def get_today_sessions(db: Session, target_date: Optional[date] = None) -> list[TodaySessionDTO]:
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
    return [TodaySessionDTO(**r._mapping) for r in rows]


def get_today_unpaid_attendees(db: Session, target_date: Optional[date] = None) -> list[UnpaidAttendeeDTO]:
    """Students who attended today but have debt (P6: account balance < 0) on any enrollment."""
    if target_date is None:
        target_date = date.today()
    stmt = text("""
        SELECT DISTINCT
            st.id AS student_id,
            st.full_name AS student_name,
            g.full_name AS parent_name,
            g.phone_primary,
            SUM(CASE WHEN vb.balance < 0 THEN -vb.balance ELSE 0 END)
                OVER (PARTITION BY st.id) AS total_balance
        FROM attendance a
        JOIN sessions s ON a.session_id = s.id
        JOIN students st ON a.student_id = st.id
        JOIN v_enrollment_balance vb ON vb.student_id = st.id
        LEFT JOIN student_parents sg ON sg.student_id = st.id AND sg.is_primary = TRUE
        LEFT JOIN parents g ON g.id = sg.parent_id
        WHERE s.session_date = :target_date
          AND a.status IN ('present', 'late')
          AND vb.balance < 0
        ORDER BY total_balance DESC
    """)
    rows = db.execute(stmt, {"target_date": str(target_date)}).all()
    return [UnpaidAttendeeDTO(**r._mapping) for r in rows]


def get_group_roster(db: Session, group_id: int, level_number: int) -> list[GroupRosterRowDTO]:
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
    return [GroupRosterRowDTO(**r._mapping) for r in rows]


def get_attendance_heatmap(db: Session, group_id: int, level_number: int) -> list[AttendanceHeatmapRowDTO]:
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
    return [AttendanceHeatmapRowDTO(**r._mapping) for r in rows]


def get_student_progress(
    db: Session, 
    student_id: Optional[int] = None, 
    group_id: Optional[int] = None
) -> list[StudentProgressDTO]:
    """Student progress analytics for all or specific student/group."""
    # Build the WHERE clause dynamically
    where_conditions = ["en.status = 'active'"]
    params = {}
    
    if student_id:
        where_conditions.append("st.id = :student_id")
        params["student_id"] = student_id
    
    if group_id:
        where_conditions.append("en.group_id = :group_id")
        params["group_id"] = group_id
    
    where_clause = " AND ".join(where_conditions)
    
    stmt = text(f"""
        SELECT
            st.id AS student_id,
            st.full_name AS student_name,
            c.name AS course_name,
            g.name AS group_name,
            en.level_number AS current_level,
            COALESCE(vgs.total_sessions, 0) AS total_sessions,
            COALESCE(att.sessions_attended, 0) AS sessions_attended,
            COALESCE(att.sessions_missed, 0) AS sessions_missed,
            CASE
                WHEN COALESCE(vgs.total_sessions, 0) = 0 THEN 0
                ELSE ROUND(
                    100.0 * COALESCE(att.sessions_attended, 0) / vgs.total_sessions, 1
                )
            END AS attendance_pct,
            CASE
                WHEN COALESCE(att.sessions_attended, 0) >= COALESCE(vgs.total_sessions, 0) * 0.8 
                    THEN 'on_track'
                WHEN COALESCE(att.sessions_attended, 0) >= COALESCE(vgs.total_sessions, 0) * 0.6 
                    THEN 'at_risk'
                ELSE 'behind'
            END AS progress_status,
            NULL AS estimated_completion_date,
            en.created_at::date AS enrollment_date,
            NULL AS last_attendance_date
        FROM enrollments en
        JOIN students st ON en.student_id = st.id
        JOIN groups g ON en.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN v_enrollment_attendance att ON att.enrollment_id = en.id
        LEFT JOIN v_group_session_count vgs ON vgs.group_id = en.group_id
            AND vgs.level_number = en.level_number
        WHERE {where_clause}
        ORDER BY st.full_name, c.name
    """)
    
    rows = db.execute(stmt, params).all()
    return [StudentProgressDTO(**r._mapping) for r in rows]


def get_course_completion(db: Session) -> list[CourseCompletionDTO]:
    """Course completion rates analysis per course."""
    stmt = text("""
        SELECT 
            c.id as course_id,
            c.name as course_name,
            COUNT(e.id) FILTER (WHERE e.status = 'active' OR e.status = 'completed') as started_count,
            COUNT(e.id) FILTER (WHERE e.status = 'completed') as completed_count,
            COUNT(e.id) FILTER (WHERE e.status = 'dropped') as dropped_count,
            COUNT(e.id) FILTER (WHERE e.status = 'active') as in_progress_count,
            CASE 
                WHEN COUNT(e.id) FILTER (WHERE e.status = 'active' OR e.status = 'completed') = 0 
                THEN 0
                ELSE ROUND(
                    100.0 * COUNT(e.id) FILTER (WHERE e.status = 'completed') 
                    / COUNT(e.id) FILTER (WHERE e.status = 'active' OR e.status = 'completed'), 1
                )
            END as completion_pct,
            NULL as avg_days_to_complete
        FROM courses c
        LEFT JOIN groups g ON g.course_id = c.id
        LEFT JOIN enrollments e ON e.group_id = g.id
        GROUP BY c.id, c.name
        HAVING COUNT(e.id) > 0
        ORDER BY completion_pct DESC
    """)
    rows = db.execute(stmt).all()
    return [CourseCompletionDTO(**r._mapping) for r in rows]
