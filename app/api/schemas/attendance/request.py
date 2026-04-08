"""
app/api/schemas/attendance/request.py
─────────────────────────────────────
Attendance-related request schemas.

Input validation models for attendance marking operations,
extraction from router files to enforce SOLID separation of concerns.
"""
from typing import Literal
from pydantic import BaseModel


class StudentAttendanceUpdate(BaseModel):
    """
    Single student attendance update.
    """
    student_id: int
    status: Literal["present", "absent", "cancelled"]


class MarkAttendanceRequest(BaseModel):
    """
    Body for POST /attendance/session/{session_id}/mark.
    updates is a list of student attendance updates.
    """
    updates: list[StudentAttendanceUpdate]

