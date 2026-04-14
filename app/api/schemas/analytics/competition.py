"""
app/api/schemas/analytics/competition.py
────────────────────────────────────────
API DTOs for Competition analytics responses.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class CompetitionFeeSummaryResponse(BaseModel):
    """Participation and fee summary for a competition."""
    competition_id: int
    competition_name: str
    competition_date: Optional[date]
    team_count: int
    member_count: int
    fees_collected: float
    fees_outstanding: float

    model_config = {"from_attributes": True}
