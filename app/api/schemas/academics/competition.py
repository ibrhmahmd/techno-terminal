"""
app/api/schemas/academics/competition.py
────────────────────────────────────────
Public-facing Competition Response DTOs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
