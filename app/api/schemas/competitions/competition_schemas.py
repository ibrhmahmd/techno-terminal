"""
app/api/schemas/competitions/competition_schemas.py
────────────────────────────────────────────────────
API-facing Competition Response DTOs.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.competitions.schemas.competition_schemas import CompetitionDTO
from app.modules.competitions.schemas.team_schemas import CategoryWithTeamsDTO


class CategoryResponse(BaseModel):
    """Category info for API response (3-table schema)."""
    category: str
    subcategories: list[str]


class UpdateCompetitionInput(BaseModel):
    """Input for updating a competition (partial updates supported)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    edition: Optional[str] = Field(None, max_length=100)
    edition_year: Optional[int] = Field(None, ge=2000, le=2100)
    competition_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=200)
    fee_per_student: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=1000)


class CompetitionSummaryResponse(BaseModel):
    """Full competition summary with nested data."""
    competition: CompetitionDTO
    categories: list[CategoryWithTeamsDTO]
    total_teams: int
    total_participants: int
