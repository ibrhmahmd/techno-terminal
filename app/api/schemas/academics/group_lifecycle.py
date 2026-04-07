"""
app/api/schemas/academics/group_lifecycle.py
───────────────────────────────────────────
Pydantic models for group lifecycle API requests/responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class CancelLevelInput(BaseModel):
    """Input schema for cancelling a group level."""
    reason: str | None = Field(
        None,
        max_length=500,
        description="Optional reason for cancellation"
    )


class CancelLevelResult(BaseModel):
    """Response schema for cancelled level."""
    level_id: int
    level_number: int
    status: str
    cancelled_at: datetime
    reason: str | None


class GroupLevelDTO(BaseModel):
    """DTO for group level information."""
    id: int
    group_id: int
    level_number: int
    course_id: int
    course_name: str | None
    instructor_id: int | None
    instructor_name: str | None
    sessions_planned: int
    price_override: float | None
    status: str
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime


class UpdateGroupLevelDTO(BaseModel):
    """Input schema for updating a group level."""
    course_id: int | None = Field(None, gt=0)
    instructor_id: int | None = Field(None, gt=0)
    sessions_planned: int | None = Field(None, gt=0)
    price_override: float | None = Field(None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
