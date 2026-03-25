"""
app/modules/attendance/schemas/attendance_schemas.py
────────────────────────────────────────────────────
Typed input and output DTOs for the Attendance service layer.
"""
from typing import Literal, Optional
from pydantic import BaseModel

AttendanceStatus = Literal["present", "absent", "late", "excused"]

class MarkAttendanceInput(BaseModel):
    """
    Input for attendance_service.mark_session_attendance().
    student_statuses maps student_id → attendance status.
    """
    session_id: int
    student_statuses: dict[int, AttendanceStatus]
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
