"""
app/modules/attendance/schemas/attendance_schemas.py
────────────────────────────────────────────────────
Typed input and output DTOs for the Attendance service layer.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

AttendanceStatus = Literal["present", "absent", "cancelled"]


class StudentAttendanceItem(BaseModel):
    """Individual student attendance entry for marking."""
    student_id: int = Field(..., gt=0, description="Student ID must be positive")
    status: AttendanceStatus = Field(..., description="Attendance status: present, absent, or cancelled")


class MarkAttendanceInput(BaseModel):
    """
    Input for attendance_service.mark_session_attendance().
    entries is a typed list of student attendance items.
    """
    session_id: int
    entries: list[StudentAttendanceItem]
    marked_by_user_id: Optional[int] = None


class SessionAttendanceRowDTO(BaseModel):
    """Output DTO for a student's attendance in a single session."""
    student_id: int
    status: AttendanceStatus


class EnrollmentAttendanceSummaryDTO(BaseModel):
    """Output DTO for the total attendance stats of an enrollment."""
    enrollment_id: int
    sessions_attended: int
    sessions_missed: int


class MarkAttendanceResponseDTO(BaseModel):
    """Output DTO detailing how many records were affected."""
    marked: int
    skipped: list[int]
