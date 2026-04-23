from typing import Sequence, List
from sqlmodel import Session, select
from sqlalchemy import text
from app.modules.attendance.models import Attendance
from app.modules.attendance.schemas import EnrollmentAttendanceSummaryDTO, StudentEnrollmentAttendanceDTO, SessionAttendanceRecord


def upsert_attendance(session: Session, record: Attendance) -> Attendance:
    """Insert or update attendance on UNIQUE(student_id, session_id)."""
    stmt = text("""
        INSERT INTO attendance (student_id, session_id, enrollment_id, status, marked_by, marked_at)
        VALUES (:student_id, :session_id, :enrollment_id, :status, :marked_by, NOW())
        ON CONFLICT (student_id, session_id)
        DO UPDATE SET status = EXCLUDED.status,
                      marked_by = EXCLUDED.marked_by,
                      marked_at = NOW()
        RETURNING id
    """)
    session.execute(
        stmt,
        {
            "student_id": record.student_id,
            "session_id": record.session_id,
            "enrollment_id": record.enrollment_id,
            "status": record.status,
            "marked_by": record.marked_by,
        },
    )
    return record


def get_session_attendance(session: Session, session_id: int) -> Sequence[Attendance]:
    stmt = select(Attendance).where(Attendance.session_id == session_id)
    return session.exec(stmt).all()


def get_enrollment_attendance(session: Session, enrollment_id: int) -> EnrollmentAttendanceSummaryDTO:
    """Queries the v_enrollment_attendance view for summary stats."""
    stmt = text("""
        SELECT enrollment_id, sessions_attended, sessions_missed
        FROM v_enrollment_attendance
        WHERE enrollment_id = :enrollment_id
    """)
    result = session.execute(stmt, {"enrollment_id": enrollment_id}).first()
    if result:
        return EnrollmentAttendanceSummaryDTO(**result._mapping)
    return EnrollmentAttendanceSummaryDTO(
        enrollment_id=enrollment_id,
        sessions_attended=0,
        sessions_missed=0,
    )


def get_student_attendance_summary(
    session: Session, student_id: int
) -> List[StudentEnrollmentAttendanceDTO]:
    """
    Get attendance for a student grouped by enrollment.
    Returns list of DTOs with all session dates per group+level.

    Uses raw SQL with json_agg to collect all sessions per enrollment.
    """
    stmt = text("""
        SELECT
            e.id as enrollment_id,
            g.id as group_id,
            g.name as group_name,
            c.name as course_name,
            e.level_number,
            COUNT(*) FILTER (WHERE a.status IN ('present', 'late')) as present_count,
            COUNT(*) FILTER (WHERE a.status = 'absent') as absent_count,
            COALESCE(
                json_agg(
                    json_build_object(
                        'session_date', s.session_date,
                        'status', a.status
                    ) ORDER BY s.session_date
                ) FILTER (WHERE s.session_date IS NOT NULL),
                '[]'
            ) as sessions
        FROM attendance a
        JOIN sessions s ON a.session_id = s.id
        JOIN enrollments e ON a.enrollment_id = e.id
        JOIN groups g ON e.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        WHERE a.student_id = :student_id
        GROUP BY e.id, g.id, g.name, c.name, e.level_number
        ORDER BY e.created_at DESC
    """)

    result = session.execute(stmt, {"student_id": student_id})
    rows = result.mappings().all()

    dtos = []
    for row in rows:
        import json
        sessions_raw = row["sessions"]
        if isinstance(sessions_raw, str):
            sessions_list = json.loads(sessions_raw)
        else:
            sessions_list = sessions_raw or []

        sessions = [
            SessionAttendanceRecord(
                session_date=s["session_date"],
                status=s["status"]
            )
            for s in sessions_list
        ]

        dtos.append(StudentEnrollmentAttendanceDTO(
            enrollment_id=row["enrollment_id"],
            group_id=row["group_id"],
            group_name=row["group_name"],
            course_name=row["course_name"],
            level_number=row["level_number"],
            present_count=row["present_count"],
            absent_count=row["absent_count"],
            sessions=sessions
        ))

    return dtos


def get_attendance_for_group_level(
    session: Session, group_id: int, level_number: int
) -> Sequence[Attendance]:
    """
    Get all attendance records for a specific group level.
    Used by the attendance grid endpoint.
    """
    from app.modules.academics.models.session_models import CourseSession
    
    # Join through sessions to get attendance for this group/level
    stmt = (
        select(Attendance)
        .join(CourseSession, Attendance.session_id == CourseSession.id)
        .where(CourseSession.group_id == group_id)
        .where(CourseSession.level_number == level_number)
    )
    return session.exec(stmt).all()


# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Note: Attendance is upsert-only (no separate insert/update).
create = upsert_attendance
list_all = get_session_attendance
