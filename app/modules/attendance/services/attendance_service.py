from app.db.uow import UnitOfWork
from app.modules.attendance.models.attendance_models import Attendance
from app.modules.attendance.repositories.attendance_repository import AttendanceRepository
from app.modules.attendance.schemas.attendance_schemas import (
    MarkAttendanceResponseDTO,
    SessionAttendanceRowDTO,
    StudentAttendanceItem,
)
from app.shared.exceptions import NotFoundError


class AttendanceService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._attendance = AttendanceRepository(uow.session)

    def mark_session_attendance(
        self,
        session_id: int,
        entries: list[StudentAttendanceItem],
        marked_by_user_id: int | None = None,
    ) -> MarkAttendanceResponseDTO:
        """
        Marks attendance for a whole session in one operation.
        """
        course_session = self._attendance.get_course_session(session_id)
        if not course_session:
            raise NotFoundError(f"Session ID {session_id} not found.")

        group_id = course_session.group_id
        level_number = course_session.level_number

        marked = 0
        skipped = []

        for entry in entries:
            enrollment = self._attendance.get_active_enrollment(entry.student_id, group_id)
            if not enrollment or enrollment.level_number != level_number:
                skipped.append(entry.student_id)
                continue

            record = Attendance(
                student_id=entry.student_id,
                session_id=session_id,
                enrollment_id=enrollment.id,
                status=entry.status,
                marked_by=marked_by_user_id,
            )
            self._attendance.upsert_attendance(record)
            marked += 1

        self._uow.commit()
        return MarkAttendanceResponseDTO(marked=marked, skipped=skipped)

    def get_session_roster_with_attendance(self, session_id: int) -> list[SessionAttendanceRowDTO]:
        """
        Returns existing attendance rows for a session as securely typed DTOs.
        """
        rows = self._attendance.get_session_attendance(session_id)
        return [SessionAttendanceRowDTO(student_id=r.student_id, status=r.status) for r in rows]
