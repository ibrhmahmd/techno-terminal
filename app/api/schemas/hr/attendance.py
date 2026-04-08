"""
app/api/schemas/hr/attendance.py
────────────────────────────────
HR Attendance DTOs.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AttendanceLogInput(BaseModel):
    """
    Input for logging employee attendance.
    """
    employee_id: int
    status: str  # present, absenti 
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class AttendanceLogOutput(BaseModel):
    """
    Output for attendance log confirmation.
    """
    employee_id: int
    status: str
    logged_at: datetime
    message: str

    model_config = {"from_attributes": True}
