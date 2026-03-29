"""
app/modules/competitions/schemas/team_schemas.py
─────────────────────────────────────────────────
Typed DTOs for Teams, Team Members, and complex cross-entity responses.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.shared.validators import validate_non_empty_string
from app.modules.competitions.schemas.competition_schemas import CompetitionDTO, CompetitionCategoryDTO


# ── Internal Output DTOs ──────────────────────────────────────────────────

class TeamDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    group_id: Optional[int] = None
    team_name: str
    coach_id: Optional[int] = None
    enrollment_fee_per_student: Optional[float] = None
    created_at: Optional[datetime] = None


class TeamMemberDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int
    student_id: int
    fee_paid: bool = False
    payment_id: Optional[int] = None


# ── Service Input Command DTOs ────────────────────────────────────────────

class RegisterTeamInput(BaseModel):
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
            raise ValueError("At least one student is required.")
        return v
        
    @field_validator("team_name", mode="before")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return validate_non_empty_string(v, field="team name")


class PayCompetitionFeeInput(BaseModel):
    team_id: int
    student_id: int
    parent_id: Optional[int] = None
    received_by_user_id: Optional[int] = None


# ── Complex Service Aggregate Output DTOs ─────────────────────────────────

class StudentCompetitionDTO(BaseModel):
    """Returned by get_student_competitions"""
    membership: TeamMemberDTO
    team: TeamDTO
    category: CompetitionCategoryDTO
    competition: Optional[CompetitionDTO] = None


class TeamRegistrationResultDTO(BaseModel):
    """Returned by register_team"""
    team: TeamDTO
    members_added: int


class AddTeamMemberResultDTO(BaseModel):
    """Returned by add_team_member_to_existing"""
    team_member_id: int
    student_id: int
    student_name: str


class TeamMemberRosterDTO(BaseModel):
    """Returned by list_team_members"""
    team_member_id: int
    student_id: int
    student_name: str
    fee_paid: bool
    payment_id: Optional[int] = None


class PayCompetitionFeeResponseDTO(BaseModel):
    """Returned by pay_competition_fee"""
    receipt_number: str
    payment_id: int
    amount: float


# Nested DTOs for the massive get_competition_summary

class TeamWithMembersDTO(BaseModel):
    team: TeamDTO
    members: list[TeamMemberDTO]


class CategoryWithTeamsDTO(BaseModel):
    category: CompetitionCategoryDTO
    teams: list[TeamWithMembersDTO]


class CompetitionSummaryDTO(BaseModel):
    """Returned by get_competition_summary"""
    competition: CompetitionDTO
    categories: list[CategoryWithTeamsDTO]
