"""
app/api/schemas/academics/group_level.py
──────────────────────────────────────────
Public-facing Group Level DTOs.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class GroupLevelPublic(BaseModel):
    """Group level response DTO."""
    id: int
    group_id: int
    level_number: int
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    sessions_planned: int
    price_override: Optional[float] = None
    status: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupLevelScheduleResponse(BaseModel):
    """Response for scheduling a new level."""
    level: GroupLevelPublic
    sessions_created: int
    sessions: list[dict]  # SessionSummary
    message: str


class GroupLevelCompletionResponse(BaseModel):
    """Response for completing a level."""
    completed_level: dict  # GroupLevelSummary
    new_level: dict  # GroupLevelSummary
    message: str


class GroupLevelSummary(BaseModel):
    """Slim group level for list/nested responses."""
    id: int
    group_id: int
    level_number: int
    status: str
    course_name: Optional[str] = None
    instructor_name: Optional[str] = None

    model_config = {"from_attributes": True}
