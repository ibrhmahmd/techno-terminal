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
    DashboardSummaryDTO,
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
    RetentionCohortDTO,
)
from .dashboard_schemas import (
    GroupSessionInfoDTO,
    GroupMetadataResultDTO,
    InstructorInfoDTO,
    GroupInfoDTO,
    AttendanceRecordDTO,
    SessionWithAttendanceDTO,
    TodaySessionDTO as DashboardTodaySessionDTO,
    CurrentLevelDTO,
    ScheduledGroupDTO,
    DashboardSummaryDTO as DashboardOverviewSummaryDTO,
    DashboardDailyOverviewDTO,
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
    "DashboardSummaryDTO",

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
    "RetentionCohortDTO",

    # Dashboard
    "GroupSessionInfoDTO",
    "GroupMetadataResultDTO",
    "InstructorInfoDTO",
    "GroupInfoDTO",
    "AttendanceRecordDTO",
    "SessionWithAttendanceDTO",
    "DashboardTodaySessionDTO",
    "CurrentLevelDTO",
    "ScheduledGroupDTO",
    "DashboardOverviewSummaryDTO",
    "DashboardDailyOverviewDTO",
]
