"""
app/modules/academics/schemas/group_schemas.py
───────────────────────────────────────────────
Input DTOs and typed read models for the Group entity.
"""
from datetime import time
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
    status: Optional[str] = None


# ── Typed Read Models ─────────────────────────────────────────────────────────

class EnrichedGroupDTO(BaseModel):
    """Typed read model for enriched group SQL query rows."""
    id: int
    group_name: str
    course_name: str
    instructor_name: str
    level_number: int
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None
    default_time_end: Optional[time] = None
    max_capacity: Optional[int] = None
    status: str
