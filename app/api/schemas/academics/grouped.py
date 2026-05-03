"""
app/api/schemas/academics/grouped.py
────────────────────────────────────
Public-facing Grouped Groups DTOs.
"""
from enum import Enum

from pydantic import BaseModel


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
    groups: list[dict]  # EnrichedGroupPublic - will be imported as Any to avoid circular import #TODO remove Dict and write a typed DTO class


class GroupedGroupsResponse(BaseModel):
    """Response for grouped groups endpoint."""
    groups: list[GroupedItem]
    total: int
    group_by: str
