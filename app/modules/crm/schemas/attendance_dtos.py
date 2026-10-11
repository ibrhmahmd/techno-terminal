"""
app/modules/crm/schemas/attendance_dtos.py
──────────────────────────────────────────
CRM-owned attendance DTOs for student profile.
These mirror the attendance module's DTOs but live in CRM per ADR-0004.
"""
from datetime import date
from typing import List
from pydantic import BaseModel


class SessionAttendanceRecord(BaseModel):
    """Single session attendance record with date and status."""
    session_date: date
    status: str  # present, absent, cancelled, or null if not marked

    model_config = {"from_attributes": True}


class StudentEnrollmentAttendanceDTO(BaseModel):
    """
    Per-enrollment attendance summary with all session records.
    Used for student profile attendance display.
    """
    enrollment_id: int
    group_id: int
    group_name: str
    course_name: str
    level_number: int
    present_count: int
    absent_count: int
    sessions: List[SessionAttendanceRecord]

    model_config = {"from_attributes": True}