"""
app/modules/competitions/schemas/competition_schemas.py
─────────────────────────────────────────────────
Typed DTOs for Competitions and Categories.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.shared.validators import validate_non_empty_string


# ── Competition Output DTOs ──────────────────────────────────────────────

class CompetitionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    edition: Optional[str] = None
    competition_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class CompetitionCategoryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    competition_id: int
    category_name: str
    notes: Optional[str] = None


# ── Competition Input Command DTOs ───────────────────────────────────────

class CreateCompetitionInput(BaseModel):
    name: str
    edition: Optional[str] = None
    competition_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return validate_non_empty_string(v, field="competition name")


class AddCategoryInput(BaseModel):
    competition_id: int
    category_name: str
    notes: Optional[str] = None

    @field_validator("category_name", mode="before")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return validate_non_empty_string(v, field="category name")
