"""
app/modules/analytics/schemas/academic_schemas.py
─────────────────────────────────────────────────
Data Transfer Objects (DTOs) for the Academic analytics domain.
"""

from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class TodaySessionDTO(BaseModel):
    session_id: int
    session_date: date
    start_time: time
    end_time: time
    session_number: int
    level_number: int
    group_id: int
    course_name: str
    group_name: str
    instructor_name: str
    present: int
    absent: int
    unmarked: int
    total_enrolled: int


class UnpaidAttendeeDTO(BaseModel):
    student_id: int
    student_name: str
    parent_name: Optional[str]
    phone_primary: Optional[str]
    total_balance: float


class GroupRosterRowDTO(BaseModel):
    student_id: int
    student_name: str
    enrollment_id: int
    enrollment_status: str
    balance: float
    sessions_attended: int
    sessions_missed: int
    total_sessions: int
    attendance_pct: float


class AttendanceHeatmapRowDTO(BaseModel):
    student_id: int
    student_name: str
    session_id: int
    session_number: int
    session_date: date
    status: str


class StudentProgressDTO(BaseModel):
    """Student progress analytics for a specific enrollment."""
    student_id: int
    student_name: str
    course_name: str
    group_name: str
    current_level: int
    total_sessions: int
    sessions_attended: int
    sessions_missed: int
    attendance_pct: float
    progress_status: str  # "on_track", "at_risk", "behind"
    estimated_completion_date: Optional[date]
    enrollment_date: date
    last_attendance_date: Optional[date]


class CourseCompletionDTO(BaseModel):
    """Course completion rates analysis."""
    course_id: int
    course_name: str
    started_count: int
    completed_count: int
    dropped_count: int
    in_progress_count: int
    completion_pct: float
    avg_days_to_complete: Optional[float]
