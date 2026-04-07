"""
app/modules/analytics/schemas/competition_schemas.py
────────────────────────────────────────────────────
Data Transfer Objects (DTOs) for the Competition analytics domain.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class CompetitionFeeSummaryDTO(BaseModel):
    competition_id: int
    competition_name: str
    competition_date: Optional[date]
    team_count: int
    member_count: int
    fees_collected: float
    fees_outstanding: float
