from app.db.connection import get_session
from app.modules.enrollments.enrollment_repository import get_active_enrollment
from app.modules.academics.models import CourseSession
from app.modules.attendance.models import Attendance
from app.modules.attendance.schemas import (
    SessionAttendanceRowDTO,
    EnrollmentAttendanceSummaryDTO,
    MarkAttendanceResponseDTO,
)
from app.shared.exceptions import NotFoundError
from app.modules.attendance import repositories as repo


class AttendanceService:
    def mark_session_attendance(
        self,
        session_id: int,
        student_statuses: dict[int, str],
        marked_by_user_id: int | None = None,
    ) -> MarkAttendanceResponseDTO:
        """
        Marks attendance for a whole session in one operation.
        """
        with get_session() as session:
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

            return MarkAttendanceResponseDTO(marked=marked, skipped=skipped)

    def get_session_roster_with_attendance(self, session_id: int) -> list[SessionAttendanceRowDTO]:
        """
        Returns existing attendance rows for a session as securely typed DTOs.
        """
        with get_session() as session:
            rows = repo.get_session_attendance(session, session_id)
            return [SessionAttendanceRowDTO(student_id=r.student_id, status=r.status) for r in rows]

    def get_attendance_summary(self, enrollment_id: int) -> EnrollmentAttendanceSummaryDTO:
        """Returns sessions_attended and sessions_missed wrapped in a DTO."""
        with get_session() as session:
            return repo.get_enrollment_attendance(session, enrollment_id)
