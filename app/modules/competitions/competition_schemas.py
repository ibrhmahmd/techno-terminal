"""
app/modules/competitions/competition_schemas.py
─────────────────────────────────────────────────
Typed input DTOs for the Competitions service layer.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator
from app.shared.validators import validate_non_empty_string


class CreateCompetitionInput(BaseModel):
    """Input for competition_service.create_competition()."""
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
    """Input for competition_service.add_category()."""
    competition_id: int
    category_name: str
    notes: Optional[str] = None

    @field_validator("category_name", mode="before")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return validate_non_empty_string(v, field="category name")


class RegisterTeamInput(BaseModel):
    """Input for competition_service.register_team()."""
    category_id: int
    team_name: str
    student_ids: list[int]
    coach_id: Optional[int] = None
    group_id: Optional[int] = None
    fee_per_student: Optional[float] = None

    @field_validator("student_ids")
    @classmethod
    def at_least_one_student(cls, v: list[int]) -> list[int]:
        if not v:
            from app.shared.exceptions import ValidationError
            raise ValidationError("At least one student is required.")
        return v


class PayCompetitionFeeInput(BaseModel):
    """Input for competition_service.pay_competition_fee()."""
    team_id: int
    student_id: int
    guardian_id: Optional[int] = None
    received_by_user_id: Optional[int] = None
