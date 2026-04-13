"""
app/modules/academics/schemas/group_schemas.py
───────────────────────────────────────────────
Input DTOs and typed read models for the Group entity.
"""
from datetime import date, time
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, model_validator
from app.modules.academics.constants import WEEKDAYS

WeekDay = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]


# ── Input DTOs ────────────────────────────────────────────────────────────────

class ScheduleGroupInput(BaseModel):
    """Input for GroupService.schedule_group()."""
    course_id: int
    instructor_id: int
    default_day: WeekDay
    default_time_start: time
    default_time_end: time
    notes: Optional[str] = None
    max_capacity: int = 15

    @model_validator(mode="after")
    def validate_time_window(self) -> "ScheduleGroupInput":
        """Reuse the module time window check (11AM–9PM) from helpers — no import from service."""
        from app.modules.academics.helpers.time_helpers import validate_times
        validate_times(self.default_time_start, self.default_time_end)
        return self


class UpdateGroupDTO(BaseModel):
    """Partial update DTO for GroupService.update_group()."""
    name: Optional[str] = None
    course_id: Optional[int] = None
    level_number: Optional[int] = None
    max_capacity: Optional[int] = None
    instructor_id: Optional[int] = None
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None
    default_time_end: Optional[time] = None
    notes: Optional[str] = None
    status: Optional[str] = None


# ── Group Level Management DTOs ───────────────────────────────────────────────

class ScheduleGroupLevelInput(BaseModel):
    """Input for scheduling a new level for an existing group."""
    group_id: int
    level_number: int = 1
    instructor_id: Optional[int] = None  # Override group's default instructor
    price_override: Optional[Decimal] = None  # None/0 uses course default price
    start_date: Optional[date] = None  # Default: next weekday from today


class ProgressGroupLevelInput(BaseModel):
    """Input for progressing a group to the next level."""
    group_id: int
    price_override: Optional[Decimal] = None  # None/0 uses course default price


class ProgressGroupLevelResult(BaseModel):
    """Result of progressing a group to the next level."""
    old_level_number: int
    new_level_number: int
    enrollments_migrated: int
    sessions_created: int
    message: str


# ── Typed Read Models ─────────────────────────────────────────────────────────

class EnrichedGroupDTO(BaseModel):
    """Typed read model for enriched group SQL query rows."""
    id: int
    group_name: str
    course_id: int
    course_name: str
    instructor_id: Optional[int] = None
    instructor_name: str
    level_number: int
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None
    default_time_end: Optional[time] = None
    max_capacity: Optional[int] = None
    notes: Optional[str] = None
    status: str
    current_student_count: int 
