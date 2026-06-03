"""
app/api/schemas/academics/grouped.py
────────────────────────────────────
Public-facing Grouped Groups DTOs.
"""
from enum import Enum

from pydantic import BaseModel
from app.api.schemas.academics.group import EnrichedGroupPublic


class GroupByField(str, Enum):
    """Fields that groups can be grouped by."""
    DAY = "day"
    COURSE = "course"
    INSTRUCTOR = "instructor"
    STATUS = "status"


class GroupedItem(BaseModel):
    """A single grouped item containing groups under a specific key."""
    key: str
    label: str
    count: int
    groups: list[EnrichedGroupPublic]


class GroupedGroupsResponse(BaseModel):
    """Response for grouped groups endpoint."""
    groups: list[GroupedItem]
    total: int
    group_by: str
