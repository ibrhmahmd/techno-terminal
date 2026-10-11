from typing import Sequence

from sqlalchemy import text
from sqlmodel import Session, select

from app.modules.academics.models.session_models import CourseSession
from app.modules.attendance.models import Attendance
from app.modules.enrollments.models.enrollment_models import Enrollment


class AttendanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_course_session(self, session_id: int) -> CourseSession | None:
        return self._session.get(CourseSession, session_id)

    def get_active_enrollment(self, student_id: int, group_id: int) -> Enrollment | None:
        stmt = (
            select(Enrollment)
            .where(Enrollment.student_id == student_id)
            .where(Enrollment.group_id == group_id)
            .where(Enrollment.status == "active")
        )
        return self._session.exec(stmt).first()

    def upsert_attendance(self, record: Attendance) -> Attendance:
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
        self._session.execute(
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

    def get_session_attendance(self, session_id: int) -> Sequence[Attendance]:
        stmt = select(Attendance).where(Attendance.session_id == session_id)
        return self._session.exec(stmt).all()
