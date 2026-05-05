"""
app/api/schemas/academics/group.py
────────────────────────────────────
Public-facing Group DTOs.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from app.shared.datetime_utils import time_to_str


class GroupPublic(BaseModel):
    """
    Full group profile returned by GET /academics/groups/{id}.
    """

    id: int
    name: str
    course_id: int
    instructor_id: Optional[int] = None
    level_number: int
    max_capacity: Optional[int] = None
    default_day: Optional[str] = None
    default_time_start: Optional[str] = None
    default_time_end: Optional[str] = None
    status: str = "active"

    model_config = {"from_attributes": True}

    @field_validator("default_time_start", "default_time_end", mode="before")
    @classmethod
    def parse_time(cls, value):
        return time_to_str(value)


class GroupListItem(BaseModel):
    """
    Slim group for list endpoints — includes denormalized names for display.
    """

    id: int
    name: str
    course_id: int
    level_number: int
    default_day: Optional[str] = None
    default_time_start: Optional[str] = None
    status: str = "active"

    model_config = {"from_attributes": True}

    @field_validator("default_time_start", mode="before")
    @classmethod
    def parse_time(cls, value):
        return time_to_str(value)


class EnrichedGroupPublic(BaseModel):
    """
    Group profile with denormalized instructor and course names.
    Returned by enriched group endpoints.
    """
    id: int
    group_name: str
    course_id: int
    course_name: str
    instructor_id: Optional[int] = None
    instructor_name: str
    level_number: int
    default_day: Optional[str] = None
    default_time_start: Optional[str] = None
    default_time_end: Optional[str] = None
    max_capacity: Optional[int] = None
    notes: Optional[str] = None
    status: str
    current_student_count: int

    model_config = {"from_attributes": True}

    @field_validator("default_time_start", "default_time_end", mode="before")
    @classmethod
    def parse_time(cls, value):
        return time_to_str(value)


# ── Group Level Management Request Schemas ────────────────────────────────────

class ProgressGroupLevelRequest(BaseModel):
    """
    Request body for POST /academics/groups/{id}/progress-level.
    Progress group to next level.
    """
    price_override: Optional[Decimal] = None  # None/0 uses course default price
    target_level: Optional[int] = None  # If None, defaults to current + 1
    auto_migrate_enrollments: bool = True  # If False, creates empty level
    complete_current_level: bool = True  # If False, keeps current level active
    instructor_id: Optional[int] = None  # Override group's default instructor
    session_start_date: Optional[date] = None  # Override default session start date (YYYY-MM-DD)
    course_id: Optional[int] = None  # Override group's course
    group_name: Optional[str] = None  # Override group name


class ProgressGroupLevelResult(BaseModel):
    """Response for POST /academics/groups/{id}/progress-level."""
    old_level_number: int
    new_level_number: int
    enrollments_migrated: int
    sessions_created: int
    message: str
