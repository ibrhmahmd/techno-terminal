"""
app/modules/academics/schemas/team_schemas.py
────────────────────────────────────────────
Internal DTOs for the Team entity.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamReadDTO(BaseModel):
    """Internal DTO for reading team data (3-table schema)."""
    id: int
    team_name: str
    competition_id: int
    category: str
    subcategory: Optional[str] = None
    group_id: Optional[int] = None
    coach_id: Optional[int] = None
    created_at: datetime
    is_deleted: bool


class TeamListResult(BaseModel):
    """Result of paginated team list query."""
    teams: list[TeamReadDTO]
    total: int
