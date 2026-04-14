"""
app/api/schemas/analytics/dashboard.py
────────────────────────────────────
Public Analytics DTOs for API responses.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    """High-level dashboard aggregates for admin view."""
    active_enrollments: int
    today_sessions_count: int

    model_config = {"from_attributes": True}


class SessionSummaryItem(BaseModel):
    """Summary of a scheduled session."""
    session_id: int
    group_id: int
    session_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    instructor_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DebtorItem(BaseModel):
    """Student with outstanding debt."""
    student_id: int
    student_name: str
    balance: float  # negative = debt

    model_config = {"from_attributes": True}
