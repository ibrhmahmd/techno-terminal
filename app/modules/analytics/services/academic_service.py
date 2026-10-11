"""
app/modules/analytics/services/academic_service.py
──────────────────────────────────────────────────
Domain service for academic analytics.
"""

from datetime import date
from typing import Optional
from app.db.uow import UnitOfWork
from app.modules.analytics.repositories.academic_repository import AcademicRepository
from app.modules.analytics.schemas import (
    UnpaidAttendeeDTO,
    AttendanceHeatmapRowDTO,
    StudentProgressDTO,
    CourseCompletionDTO,
)


class AcademicAnalyticsService:
    """Service handling attendance, sessions, and roster reporting."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = AcademicRepository(uow.session)

    def get_active_enrollment_count(self) -> int:
        return self._repo.get_active_enrollment_count()

    def get_today_unpaid_attendees(self, target_date: Optional[date] = None) -> list[UnpaidAttendeeDTO]:
        return self._repo.get_today_unpaid_attendees(target_date)

    def get_attendance_heatmap(self, group_id: int, level_number: int) -> list[AttendanceHeatmapRowDTO]:
        return self._repo.get_attendance_heatmap(group_id, level_number)

    def get_student_progress(
        self, 
        student_id: Optional[int] = None, 
        group_id: Optional[int] = None
    ) -> list[StudentProgressDTO]:
        """Get student progress analytics for all or specific student/group."""
        return self._repo.get_student_progress(student_id, group_id)

    def get_course_completion(self) -> list[CourseCompletionDTO]:
        """Get course completion rates analysis."""
        return self._repo.get_course_completion()
