"""
app/api/schemas/analytics/__init__.py
─────────────────────────────────────
Public Analytics API DTOs.
"""

# Dashboard
from .dashboard import (
    DashboardSummaryResponse,
    SessionSummaryItem,
    DebtorItem,
)

# Academic
from .academic import (
    TodaySessionItem,
    UnpaidAttendeeItem,
    GroupRosterItem,
    AttendanceHeatmapItem,
    StudentProgressItem,
    CourseCompletionItem,
)

# Financial
from .financial import (
    RevenueByDateItem,
    RevenueByMethodItem,
    OutstandingByGroupItem,
    TopDebtorItem,
    RevenueMetricsResponse,
    RevenueForecastItem,
)

# BI
from .bi import (
    EnrollmentTrendItem,
    RetentionMetricsResponse,
    InstructorPerformanceItem,
    LevelRetentionFunnelItem,
    InstructorValueMatrixItem,
    ScheduleUtilizationItem,
    FlightRiskStudentItem,
    UserEngagementItem,
    RetentionCohortItem,
)

# Competition
from .competition import CompetitionFeeSummaryResponse

__all__ = [
    # Dashboard
    "DashboardSummaryResponse",
    "SessionSummaryItem",
    "DebtorItem",

    # Academic
    "TodaySessionItem",
    "UnpaidAttendeeItem",
    "GroupRosterItem",
    "AttendanceHeatmapItem",
    "StudentProgressItem",
    "CourseCompletionItem",

    # Financial
    "RevenueByDateItem",
    "RevenueByMethodItem",
    "OutstandingByGroupItem",
    "TopDebtorItem",
    "RevenueMetricsResponse",
    "RevenueForecastItem",

    # BI
    "EnrollmentTrendItem",
    "RetentionMetricsResponse",
    "InstructorPerformanceItem",
    "LevelRetentionFunnelItem",
    "InstructorValueMatrixItem",
    "ScheduleUtilizationItem",
    "FlightRiskStudentItem",
    "UserEngagementItem",
    "RetentionCohortItem",

    # Competition
    "CompetitionFeeSummaryResponse",
]
