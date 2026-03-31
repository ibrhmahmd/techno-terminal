"""
app/api/schemas/academics/group.py
────────────────────────────────────
Public-facing Group DTOs.
"""
from typing import Optional

from pydantic import BaseModel


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
    is_active: bool = True

    model_config = {"from_attributes": True}


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
    is_active: bool = True

    model_config = {"from_attributes": True}
