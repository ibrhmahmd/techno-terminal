"""
app/modules/academics/group/core/schemas.py
───────────────────────────────────────────────
Input DTOs for the Group entity.
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


class ScheduleInput(BaseModel):
    """Nested schedule object for group creation/updates."""
    day: WeekDay
    time_start: time
    time_end: time

    @model_validator(mode="after")
    def validate_time_window(self) -> "ScheduleInput":
        from app.modules.academics.helpers.time_helpers import validate_times
        validate_times(self.time_start, self.time_end)
        return self


class ScheduleGroupInput(BaseModel):
    """Input for GroupService.schedule_group()."""
    course_id: int
    instructor_id: int
    schedule: ScheduleInput
    notes: Optional[str] = None
    max_capacity: int = 15


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


class EnrichedGroupDTO(BaseModel):
    """
    Data Transfer Object for an Enriched Group.
    Includes course and instructor names directly.
    """
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
