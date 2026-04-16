"""
app/modules/analytics/schemas/bi_schemas.py
───────────────────────────────────────────
Data Transfer Objects (DTOs) for the Business Intelligence analytics domain.
"""

from datetime import date
from pydantic import BaseModel


class EnrollmentTrendDTO(BaseModel):
    day: date
    new_enrollments: int


class RetentionMetricsDTO(BaseModel):
    course_name: str
    active_count: int
    dropped_count: int
    total_enrollments: int


class InstructorPerformanceDTO(BaseModel):
    instructor_name: str
    active_groups: int
    active_students: int


class LevelRetentionFunnelDTO(BaseModel):
    course_name: str
    level_number: int
    student_count: int


class InstructorValueMatrixDTO(BaseModel):
    instructor_name: str
    total_revenue: float
    avg_attendance_pct: float


class ScheduleUtilizationDTO(BaseModel):
    day: str
    time_start: str
    total_enrolled: int
    total_capacity: int
    utilization_pct: float


class FlightRiskStudentDTO(BaseModel):
    student_name: str
    course_name: str
    amount_owed: float
    sessions_missed: int


class RetentionCohortDTO(BaseModel):
    """Cohort-based retention analysis."""
    cohort_month: str
    initial_enrollments: int
    retention_by_month: dict[str, int]
    retention_rates: dict[str, float]
