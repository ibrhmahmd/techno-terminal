from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import text
from app.modules.attendance.models import Attendance
from app.modules.attendance.schemas import EnrollmentAttendanceSummaryDTO


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

# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Note: Attendance is upsert-only (no separate insert/update).
create = upsert_attendance
list_all = get_session_attendance
