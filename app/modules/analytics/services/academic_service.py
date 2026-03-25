"""
app/modules/analytics/services/academic_service.py
──────────────────────────────────────────────────
Domain service for academic analytics.
"""

from datetime import date
from typing import Optional
from app.db.connection import get_session
from app.modules.analytics.repositories import academic_repository as repo
from app.modules.analytics.schemas import (
    TodaySessionDTO,
    UnpaidAttendeeDTO,
    GroupRosterRowDTO,
    AttendanceHeatmapRowDTO,
)


class AcademicAnalyticsService:
    """Service handling attendance, sessions, and roster reporting."""

    def get_active_enrollment_count(self) -> int:
        with get_session() as db:
            return repo.get_active_enrollment_count(db)

    def get_today_sessions(self, target_date: Optional[date] = None) -> list[TodaySessionDTO]:
        with get_session() as db:
            return repo.get_today_sessions(db, target_date)

    def get_today_unpaid_attendees(self, target_date: Optional[date] = None) -> list[UnpaidAttendeeDTO]:
        with get_session() as db:
            return repo.get_today_unpaid_attendees(db, target_date)

    def get_group_roster(self, group_id: int, level_number: int) -> list[GroupRosterRowDTO]:
        with get_session() as db:
            return repo.get_group_roster(db, group_id, level_number)

    def get_attendance_heatmap(self, group_id: int, level_number: int) -> list[AttendanceHeatmapRowDTO]:
        with get_session() as db:
            return repo.get_attendance_heatmap(db, group_id, level_number)
