"""
app/modules/attendance/attendance_schemas.py
──────────────────────────────────────────────
Typed input DTOs for the Attendance service layer.
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
