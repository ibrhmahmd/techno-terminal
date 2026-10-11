"""
app/modules/academics/api/schemas/grouped.py
────────────────────────────────────────────
Public-facing Grouped Groups DTOs.
"""

from pydantic import BaseModel
from app.modules.academics.api.schemas.group import EnrichedGroupPublic


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
