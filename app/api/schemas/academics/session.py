"""
app/api/schemas/academics/session.py
──────────────────────────────────────
Public-facing CourseSession DTOs.
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator

from app.shared.datetime_utils import time_to_str


class SessionPublic(BaseModel):
    """
    CourseSession profile returned by session list endpoints.
    """

    id: int
    group_id: int
    level_number: int
    session_number: int
    session_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None         # scheduled | completed | cancelled
    is_extra_session: bool = False
    actual_instructor_id: Optional[int] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_time(cls, value):
        return time_to_str(value)


class DailyScheduleItem(BaseModel):
    session_id: int
    date: date
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    status: str
    notes: Optional[str] = None
    group_id: int
    group_name: str
    level_number: int
    course_id: int
    course_name: str
    enrolled_count: int = 0
    
    model_config = {"from_attributes": True}

    @field_validator("time_start", "time_end", mode="before")
    @classmethod
    def parse_time(cls, value):
        return time_to_str(value)


class GenerateLevelSessionsRequest(BaseModel):
    """Input for generating level sessions (without group_id which comes from path)."""
    level_number: int
    start_date: Optional[date] = None
