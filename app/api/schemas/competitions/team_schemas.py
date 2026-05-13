"""
app/api/schemas/competitions/team_schemas.py
────────────────────────────────────────────
API-facing Team Response DTOs.
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.competitions.schemas.team_schemas import (
    TeamDTO,
    StudentCompetitionDTO,
    TeamMemberRosterDTO,
)


class UpdateTeamInput(BaseModel):
    """Input for updating a team (partial updates supported)."""
    team_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    group_id: Optional[int] = None
    coach_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=1000)


class PlacementUpdateInput(BaseModel):
    """Input for updating team placement."""
    placement_rank: int = Field(..., ge=1, description="Placement rank (1=1st place)")
    placement_label: Optional[str] = Field(None, max_length=100, description="Label like 'Gold' or '3rd Place'")


class TeamMemberListResponse(BaseModel):
    """Response for team member list."""
    team_id: int
    team_name: str
    members: list[TeamMemberRosterDTO]


class StudentCompetitionsResponse(BaseModel):
    """Response for student's competition history."""
    student_id: int
    competitions: list[StudentCompetitionDTO]


class DeletedTeamListResponse(BaseModel):
    """Response for listing deleted teams."""
    competition_id: Optional[int]
    teams: list[TeamDTO]
    total: int
