"""
app/api/schemas/analytics/bi.py
────────────────────────────────
API DTOs for Business Intelligence analytics responses.
"""
from datetime import date
from pydantic import BaseModel


class EnrollmentTrendItem(BaseModel):
    """Daily new enrollment count."""
    day: date
    new_enrollments: int

    model_config = {"from_attributes": True}


class RetentionMetricsResponse(BaseModel):
    """Retention/dropout metrics for a course."""
    course_name: str
    active_count: int
    dropped_count: int
    total_enrollments: int

    model_config = {"from_attributes": True}


class InstructorPerformanceItem(BaseModel):
    """Performance metrics for an instructor."""
    instructor_name: str
    active_groups: int
    active_students: int

    model_config = {"from_attributes": True}


class LevelRetentionFunnelItem(BaseModel):
    """Student count at a specific course level."""
    course_name: str
    level_number: int
    student_count: int

    model_config = {"from_attributes": True}


class InstructorValueMatrixItem(BaseModel):
    """Revenue and attendance correlation for an instructor."""
    instructor_name: str
    total_revenue: float
    avg_attendance_pct: float

    model_config = {"from_attributes": True}


class ScheduleUtilizationItem(BaseModel):
    """Schedule slot utilization percentage."""
    day: str
    time_start: str
    total_enrolled: int
    total_capacity: int
    utilization_pct: float

    model_config = {"from_attributes": True}


class FlightRiskStudentItem(BaseModel):
    """Student at risk of dropping out."""
    student_name: str
    course_name: str
    amount_owed: float
    sessions_missed: int

    model_config = {"from_attributes": True}


class UserEngagementItem(BaseModel):
    """Daily user engagement metrics."""
    date: date
    daily_active_users: int
    total_sessions: int
    avg_session_duration_minutes: float
    feature_usage: dict[str, int] #TODO remove Dict and write a typed DTO class

    model_config = {"from_attributes": True}


class RetentionCohortItem(BaseModel):
    """Cohort-based retention analysis."""
    cohort_month: str
    initial_enrollments: int
    retention_by_month: dict[str, int] #TODO remove Dict and write a typed DTO class
    retention_rates: dict[str, float] #TODO remove Dict and write a typed DTO class

    model_config = {"from_attributes": True}
