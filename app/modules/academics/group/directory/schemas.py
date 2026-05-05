"""
app/modules/academics/schemas/grouped_schemas.py
────────────────────────────────────────────────
Internal DTOs for Grouped Groups.
"""
from pydantic import BaseModel

from app.modules.academics.group.core.schemas import EnrichedGroupDTO


class GroupedItemDTO(BaseModel):
    """Internal DTO for a grouped item."""
    key: str
    label: str
    count: int
    groups: list[EnrichedGroupDTO]


class GroupedGroupsResult(BaseModel):
    """Result of getting grouped groups."""
    groups: list[GroupedItemDTO]
    total: int
    group_by: str
