"""
app/modules/analytics/services/academic_service.py
──────────────────────────────────────────────────
Domain service for academic analytics.
"""

from datetime import date
from typing import Optional
from app.db.connection import get_session
import app.modules.analytics.repositories.academic_repository as repo
from app.modules.analytics.schemas import (
    UnpaidAttendeeDTO,
    AttendanceHeatmapRowDTO,
    StudentProgressDTO,
    CourseCompletionDTO,
)


class AcademicAnalyticsService:
    """Service handling attendance, sessions, and roster reporting."""

    def get_active_enrollment_count(self) -> int:
        with get_session() as db:
            return repo.get_active_enrollment_count(db)

    def get_today_unpaid_attendees(self, target_date: Optional[date] = None) -> list[UnpaidAttendeeDTO]:
        with get_session() as db:
            return repo.get_today_unpaid_attendees(db, target_date)

    def get_attendance_heatmap(self, group_id: int, level_number: int) -> list[AttendanceHeatmapRowDTO]:
        with get_session() as db:
            return repo.get_attendance_heatmap(db, group_id, level_number)

    def get_student_progress(
        self, 
        student_id: Optional[int] = None, 
        group_id: Optional[int] = None
    ) -> list[StudentProgressDTO]:
        """Get student progress analytics for all or specific student/group."""
        with get_session() as db:
            return repo.get_student_progress(db, student_id, group_id)

    def get_course_completion(self) -> list[CourseCompletionDTO]:
        """Get course completion rates analysis."""
        with get_session() as db:
            return repo.get_course_completion(db)
