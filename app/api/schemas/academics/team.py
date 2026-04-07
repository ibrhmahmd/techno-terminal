"""
app/api/schemas/academics/team.py
────────────────────────────────────
Public-facing Team DTOs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamPublic(BaseModel):
    """Team response DTO."""
    id: int
    team_name: str
    group_id: int
    coach_id: Optional[int] = None
    created_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}


class PaginatedTeamResponse(BaseModel):
    """Paginated team list response."""
    data: list[TeamPublic]
    total: int
    skip: int
    limit: int
