from app.db.connection import get_session
from app.modules.enrollments.repository import get_active_enrollment
from app.modules.academics.session_models import CourseSession
from sqlmodel import select
from app.modules.attendance.models import Attendance
from app.shared.exceptions import NotFoundError
from . import repository as repo


def mark_session_attendance(
    session_id: int,
    student_statuses: dict[
        int, str
    ],  # {student_id: "present"|"absent"|"late"|"excused"}
    marked_by_user_id: int | None = None,
) -> dict:
    """
    Marks attendance for a whole session in one operation.
    - Resolves each student's enrollment_id from the session's group+level.
    - Students without a valid active enrollment are skipped (warning, not error).
    - Upserts each attendance record.
    Returns: {"marked": count, "skipped": [student_id, ...]}
    """
    with get_session() as session:
        # Validate session exists and get group/level context
        course_session = session.get(CourseSession, session_id)
        if not course_session:
            raise NotFoundError(f"Session ID {session_id} not found.")

        group_id = course_session.group_id
        level_number = course_session.level_number

        marked = 0
        skipped = []

        for student_id, status in student_statuses.items():
            enrollment = get_active_enrollment(session, student_id, group_id)
            if not enrollment or enrollment.level_number != level_number:
                skipped.append(student_id)
                continue

            record = Attendance(
                student_id=student_id,
                session_id=session_id,
                enrollment_id=enrollment.id,
                status=status,
                marked_by=marked_by_user_id,
            )
            repo.upsert_attendance(session, record)
            marked += 1

        return {"marked": marked, "skipped": skipped}


def get_session_roster_with_attendance(session_id: int) -> list[dict]:
    """
    Returns existing attendance rows for a session as a list of dicts.
    Used by the UI to pre-fill the attendance form.
    """
    with get_session() as session:
        rows = repo.get_session_attendance(session, session_id)
        return [{"student_id": r.student_id, "status": r.status} for r in rows]


def get_attendance_summary(enrollment_id: int) -> dict:
    """Returns sessions_attended and sessions_missed from the v_enrollment_attendance view."""
    with get_session() as session:
        return repo.get_enrollment_attendance(session, enrollment_id)
