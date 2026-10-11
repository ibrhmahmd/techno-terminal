"""
app/modules/attendance/schemas/attendance_schemas.py
────────────────────────────────────────────────────
Typed input and output DTOs for the Attendance service layer.
"""
from typing import Literal
from pydantic import BaseModel, Field

AttendanceStatus = Literal["present", "absent", "cancelled"]


class StudentAttendanceItem(BaseModel):
    """Individual student attendance entry for marking."""
    student_id: int = Field(..., gt=0, description="Student ID must be positive")
    status: AttendanceStatus = Field(..., description="Attendance status: present, absent, or cancelled")


class SessionAttendanceRowDTO(BaseModel):
    """Output DTO for a student's attendance in a single session."""
    student_id: int
    status: AttendanceStatus


class MarkAttendanceResponseDTO(BaseModel):
    """Output DTO detailing how many records were affected."""
    marked: int
    skipped: list[int]
