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


class GroupCompetitionDTO(BaseModel):
    """DTO for group competition participation data."""
    participation_id: int
    competition_id: int
    competition_name: str | None = None
    category: str | None = None
    subcategory: str | None = None
    team_id: int
    team_name: str | None = None
    entered_at: datetime | None = None
    left_at: datetime | None = None
    is_active: bool
    final_placement: int | None = None
    notes: str | None = None


class WithdrawalResultDTO(BaseModel):
    """DTO for competition withdrawal result."""
    id: int
    status: str
    withdrawn_at: datetime | None = None


class TeamLinkResultDTO(BaseModel):
    """DTO for team-to-group link result."""
    team_id: int
    team_name: str | None = None
    group_id: int
