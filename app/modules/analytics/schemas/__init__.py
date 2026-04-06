"""
app/modules/analytics/schemas/__init__.py
─────────────────────────────────────────
Exports all Analytics data transfer objects.
"""

from .financial_schemas import (
    RevenueByDateDTO,
    RevenueByMethodDTO,
    OutstandingByGroupDTO,
    TopDebtorDTO,
    RevenueMetricsDTO,
    RevenueForecastDTO,
)
from .academic_schemas import (
    TodaySessionDTO,
    UnpaidAttendeeDTO,
    GroupRosterRowDTO,
    AttendanceHeatmapRowDTO,
    StudentProgressDTO,
    CourseCompletionDTO,
)
from .competition_schemas import (
    CompetitionFeeSummaryDTO,
)
from .bi_schemas import (
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

__all__ = [
    # Financial
    "RevenueByDateDTO",
    "RevenueByMethodDTO",
    "OutstandingByGroupDTO",
    "TopDebtorDTO",
    "RevenueMetricsDTO",
    "RevenueForecastDTO",

    # Academic
    "TodaySessionDTO",
    "UnpaidAttendeeDTO",
    "GroupRosterRowDTO",
    "AttendanceHeatmapRowDTO",
    "StudentProgressDTO",
    "CourseCompletionDTO",

    # Competition
    "CompetitionFeeSummaryDTO",

    # BI
    "EnrollmentTrendDTO",
    "RetentionMetricsDTO",
    "InstructorPerformanceDTO",
    "LevelRetentionFunnelDTO",
    "InstructorValueMatrixDTO",
    "ScheduleUtilizationDTO",
    "FlightRiskStudentDTO",
    "UserEngagementDTO",
    "RetentionCohortDTO",
]
