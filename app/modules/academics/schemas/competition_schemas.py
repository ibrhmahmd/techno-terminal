"""
app/modules/academics/schemas/competition_schemas.py
─────────────────────────────────────────────────────
Internal DTOs for Competition Participation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CompetitionParticipationReadDTO(BaseModel):
    """Internal DTO for reading competition participation."""
    id: int
    group_id: int
    team_id: int
    competition_id: int
    category_id: Optional[int] = None
    entered_at: datetime
    is_active: bool
    left_at: Optional[datetime] = None
    final_placement: Optional[int] = None


class CompetitionParticipationResult(BaseModel):
    """Result of competition participation operation."""
    participation: CompetitionParticipationReadDTO
    message: str
