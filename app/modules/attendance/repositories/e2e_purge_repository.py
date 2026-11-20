"""Hard delete of E2E test data in attendance's own table (#218). Staging only."""
from sqlalchemy import delete, or_
from sqlmodel import Session

from app.modules.attendance.models.attendance_models import Attendance


class AttendanceE2EPurgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def delete_for(self, student_ids: list[int], session_ids: list[int], enrollment_ids: list[int]) -> int:
        return self._session.execute(delete(Attendance).where(or_(
            Attendance.student_id.in_(student_ids),
            Attendance.session_id.in_(session_ids),
            Attendance.enrollment_id.in_(enrollment_ids),
        ))).rowcount
