"""
app/modules/analytics/services/bi_service.py
────────────────────────────────────────────
Domain service for Business Intelligence (BI) analytics.
"""

from datetime import date, timedelta
from app.db.uow import UnitOfWork
from app.modules.analytics.repositories.bi_repository import BiRepository
from app.modules.analytics.schemas import (
    EnrollmentTrendDTO,
    RetentionMetricsDTO,
    InstructorPerformanceDTO,
    LevelRetentionFunnelDTO,
    InstructorValueMatrixDTO,
    ScheduleUtilizationDTO,
    FlightRiskStudentDTO,
    RetentionCohortDTO,
)


class BIAnalyticsService:
    """Service handling high-level business intelligence, trends, and risk analysis."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = BiRepository(uow.session)

    def get_new_enrollments_trend(self, cutoff_date: date | None = None) -> list[EnrollmentTrendDTO]:
        """Get enrollment trend. Defaults to 90 days ago if cutoff not provided."""
        if cutoff_date is None:
            cutoff_date = date.today() - timedelta(days=90)
        return self._repo.get_new_enrollments_trend(cutoff_date)

    def get_retention_metrics(self) -> list[RetentionMetricsDTO]:
        return self._repo.get_retention_metrics()

    def get_instructor_performance(self) -> list[InstructorPerformanceDTO]:
        return self._repo.get_instructor_performance()

    def get_level_retention_funnel(self) -> list[LevelRetentionFunnelDTO]:
        return self._repo.get_level_retention_funnel()

    def get_instructor_value_matrix(self) -> list[InstructorValueMatrixDTO]:
        return self._repo.get_instructor_value_matrix()

    def get_schedule_utilization(self) -> list[ScheduleUtilizationDTO]:
        return self._repo.get_schedule_utilization()

    def get_flight_risk_students(self) -> list[FlightRiskStudentDTO]:
        return self._repo.get_flight_risk_students()

    def get_retention_cohorts(self, months: int = 6) -> list[RetentionCohortDTO]:
        """Get cohort-based retention analysis."""
        return self._repo.get_retention_cohorts(months)
