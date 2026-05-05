"""
app/api/schemas/academics/competition.py
────────────────────────────────────────
Public-facing Competition Response DTOs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GroupCompetitionPublic(BaseModel):
    """Full competition participation entry as returned by list endpoint."""
    participation_id: int
    competition_id: int
    competition_name: Optional[str] = None
    team_id: int
    team_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    entered_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    is_active: bool
    final_placement: Optional[int] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class TeamLinkResponse(BaseModel):
    """Response for linking a team to a group."""
    team_id: int
    team_name: Optional[str] = None
    group_id: int

    model_config = {"from_attributes": True}


class CompetitionRegistrationResponse(BaseModel):
    """Response for registering a team for competition."""
    participation_id: int
    group_id: int
    team_id: int
    competition_id: int
    category_id: Optional[int] = None
    entered_at: datetime
    is_active: bool
    message: str

    model_config = {"from_attributes": True}


class CompetitionCompletionResponse(BaseModel):
    """Response for completing competition participation."""
    participation_id: int
    is_active: bool
    left_at: Optional[datetime] = None
    final_placement: Optional[int] = None
    message: str

    model_config = {"from_attributes": True}


class CompetitionWithdrawalResponse(BaseModel):
    """Response for withdrawing from competition."""
    participation_id: int
    status: str
    withdrawn_at: datetime
    message: str

    model_config = {"from_attributes": True}
