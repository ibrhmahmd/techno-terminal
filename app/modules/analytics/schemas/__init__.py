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
)
from .academic_schemas import (
    TodaySessionDTO,
    UnpaidAttendeeDTO,
    GroupRosterRowDTO,
    AttendanceHeatmapRowDTO,
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
)

__all__ = [
    # Financial
    "RevenueByDateDTO",
    "RevenueByMethodDTO",
    "OutstandingByGroupDTO",
    "TopDebtorDTO",

    # Academic
    "TodaySessionDTO",
    "UnpaidAttendeeDTO",
    "GroupRosterRowDTO",
    "AttendanceHeatmapRowDTO",

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
]
