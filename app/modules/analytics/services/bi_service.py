"""
app/modules/analytics/services/bi_service.py
────────────────────────────────────────────
Domain service for Business Intelligence (BI) analytics.
"""

from datetime import date
from app.db.connection import get_session
import app.modules.analytics.repositories.bi_repository as repo
from app.modules.analytics.schemas import (
    EnrollmentTrendDTO,
    RetentionMetricsDTO,
    InstructorPerformanceDTO,
    LevelRetentionFunnelDTO,
    InstructorValueMatrixDTO,
    ScheduleUtilizationDTO,
    FlightRiskStudentDTO,
    UserEngagementDTO,
    RetentionCohortDTO,
)


class BIAnalyticsService:
    """Service handling high-level business intelligence, trends, and risk analysis."""

    def get_new_enrollments_trend(self, cutoff_date: date | None = None) -> list[EnrollmentTrendDTO]:
        """Get enrollment trend. Defaults to 90 days ago if cutoff not provided."""
        if cutoff_date is None:
            from datetime import timedelta
            cutoff_date = date.today() - timedelta(days=90)
        with get_session() as db:
            return repo.get_new_enrollments_trend(db, cutoff_date)

    def get_retention_metrics(self) -> list[RetentionMetricsDTO]:
        with get_session() as db:
            return repo.get_retention_metrics(db)

    def get_instructor_performance(self) -> list[InstructorPerformanceDTO]:
        with get_session() as db:
            return repo.get_instructor_performance(db)

    def get_level_retention_funnel(self) -> list[LevelRetentionFunnelDTO]:
        with get_session() as db:
            return repo.get_level_retention_funnel(db)

    def get_instructor_value_matrix(self) -> list[InstructorValueMatrixDTO]:
        with get_session() as db:
            return repo.get_instructor_value_matrix(db)

    def get_schedule_utilization(self) -> list[ScheduleUtilizationDTO]:
        with get_session() as db:
            return repo.get_schedule_utilization(db)

    def get_flight_risk_students(self) -> list[FlightRiskStudentDTO]:
        with get_session() as db:
            return repo.get_flight_risk_students(db)

    def get_user_engagement(self, days: int = 30) -> list[UserEngagementDTO]:
        """Get user engagement metrics for the specified number of days."""
        with get_session() as db:
            return repo.get_user_engagement(db, days)

    def get_retention_cohorts(self, months: int = 6) -> list[RetentionCohortDTO]:
        """Get cohort-based retention analysis."""
        with get_session() as db:
            return repo.get_retention_cohorts(db, months)
