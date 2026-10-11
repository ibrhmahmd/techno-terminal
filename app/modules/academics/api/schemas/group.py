"""
app/modules/academics/api/schemas/group.py
──────────────────────────────────────────
Public-facing Group DTOs.
"""
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
