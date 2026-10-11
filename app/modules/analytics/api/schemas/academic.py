"""
app/api/schemas/analytics/academic.py
─────────────────────────────────────
API DTOs for Academic analytics responses.
"""
from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class TodaySessionItem(BaseModel):
    """Summary of a session scheduled for today."""
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

    model_config = {"from_attributes": True}


class UnpaidAttendeeItem(BaseModel):
    """Student attending sessions today with unpaid balance."""
    student_id: int
    student_name: str
    parent_name: Optional[str]
    phone_primary: Optional[str]
    total_balance: float

    model_config = {"from_attributes": True}


class GroupRosterItem(BaseModel):
    """Student enrollment details for a group roster."""
    student_id: int
    student_name: str
    enrollment_id: int
    enrollment_status: str
    balance: float
    sessions_attended: int
    sessions_missed: int
    total_sessions: int
    attendance_pct: float

    model_config = {"from_attributes": True}


class AttendanceHeatmapItem(BaseModel):
    """Single attendance record in heatmap format."""
    student_id: int
    student_name: str
    session_id: int
    session_number: int
    session_date: date
    status: str

    model_config = {"from_attributes": True}


class StudentProgressItem(BaseModel):
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

    model_config = {"from_attributes": True}


class CourseCompletionItem(BaseModel):
    """Course completion rates analysis."""
    course_id: int
    course_name: str
    started_count: int
    completed_count: int
    dropped_count: int
    in_progress_count: int
    completion_pct: float
    avg_days_to_complete: Optional[float]

    model_config = {"from_attributes": True}
