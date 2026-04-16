"""
app/api/schemas/analytics/__init__.py
─────────────────────────────────────
Public Analytics API DTOs.
"""

# Dashboard
from app.modules.analytics.schemas.academic_schemas import TodaySessionDTO as SessionSummaryItem

# Academic
from app.modules.analytics.schemas.academic_schemas import (
    TodaySessionDTO as TodaySessionItem,
    UnpaidAttendeeDTO as UnpaidAttendeeItem,
    GroupRosterRowDTO as GroupRosterItem,
    AttendanceHeatmapRowDTO as AttendanceHeatmapItem,
    StudentProgressDTO as StudentProgressItem,
    CourseCompletionDTO as CourseCompletionItem,
)

# Financial
from app.modules.analytics.schemas.financial_schemas import (
    RevenueByDateDTO as RevenueByDateItem,
    RevenueByMethodDTO as RevenueByMethodItem,
    OutstandingByGroupDTO as OutstandingByGroupItem,
    TopDebtorDTO as TopDebtorItem,
    RevenueMetricsDTO as RevenueMetricsResponse,
    RevenueForecastDTO as RevenueForecastItem,
)

# BI
from app.modules.analytics.schemas.bi_schemas import (
    EnrollmentTrendDTO as EnrollmentTrendItem,
    RetentionMetricsDTO as RetentionMetricsResponse,
    InstructorPerformanceDTO as InstructorPerformanceItem,
    LevelRetentionFunnelDTO as LevelRetentionFunnelItem,
    InstructorValueMatrixDTO as InstructorValueMatrixItem,
    ScheduleUtilizationDTO as ScheduleUtilizationItem,
    FlightRiskStudentDTO as FlightRiskStudentItem,
    RetentionCohortDTO as RetentionCohortItem,
)

# Competition
from app.modules.analytics.schemas.competition_schemas import CompetitionFeeSummaryDTO as CompetitionFeeSummaryResponse

from pydantic import BaseModel

class DebtorItem(BaseModel):
    student_name: str
    amount_owed: float

class DashboardSummaryResponse(BaseModel):
    active_enrollments: int
    today_sessions_count: int
    sessions: list[SessionSummaryItem]
    top_debtors: list[DebtorItem] = []

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
    "RetentionCohortItem",

    # Competition
    "CompetitionFeeSummaryResponse",
]
