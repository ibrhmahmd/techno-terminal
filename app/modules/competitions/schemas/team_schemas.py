"""
app/modules/competitions/schemas/team_schemas.py
─────────────────────────────────────────────────
Typed DTOs for Teams, Team Members, and complex cross-entity responses.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.shared.validators import validate_non_empty_string
from app.modules.competitions.schemas.competition_schemas import CompetitionDTO


# ── Internal Output DTOs ──────────────────────────────────────────────────

class TeamDTO(BaseModel):
    """Team output DTO for 3-table schema."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    competition_id: int  # Direct FK to competition
    category: str  # Category name
    subcategory: Optional[str] = None  # Optional subcategory
    group_id: Optional[int] = None
    team_name: str
    coach_id: Optional[int] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    placement_rank: Optional[int] = None  # Competition placement
    placement_label: Optional[str] = None  # Placement description
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class TeamMemberDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int
    student_id: int
    amount_due: float = 0.0
    amount_paid: float = 0.0


# ── Service Input Command DTOs ────────────────────────────────────────────

class RegisterTeamInput(BaseModel):
    """Input for registering a team in 3-table schema."""
    competition_id: int  # Direct FK to competition
    team_name: str
    category: str  # Category name (citext in DB)
    subcategory: Optional[str] = None  # Optional subcategory
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    student_ids: Optional[list[int]] = None  # Optional if group_id provided
    student_fees: Optional[dict[int, float]] = None  # Per-student fees, missing defaults to 0
    coach_id: Optional[int] = None
    group_id: Optional[int] = None  # If provided, pre-fills students from group roster
    notes: Optional[str] = None  # Additional notes

    @field_validator("team_name", mode="before")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return validate_non_empty_string(v, field="team name")

    @field_validator("category", mode="before")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        return validate_non_empty_string(v, field="category")


class AddTeamMemberInput(BaseModel):
    """Input for adding a member to an existing team."""
    student_id: int
    amount_due: float = 0.0  # Fee amount due for this member


class PayCompetitionFeeInput(BaseModel):
    team_id: int
    student_id: int
    amount: float  # Payment amount (supports partial payments)
    parent_id: Optional[int] = None
    received_by_user_id: Optional[int] = None


class RefundCompetitionFeeBody(BaseModel):
    """Input for refunding a competition fee payment."""
    amount: float  # Refund amount (must not exceed amount_paid)


# ── Complex Service Aggregate Output DTOs ─────────────────────────────────

class StudentCompetitionDTO(BaseModel):
    """Returned by get_student_competitions"""
    membership: TeamMemberDTO
    team: TeamDTO
    category: str  # Category name from 3-table schema
    subcategory: Optional[str] = None
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


class TeamRegistrationResultWithWarningDTO(BaseModel):
    result: TeamRegistrationResultDTO
    warning: Optional[str] = None


class AddTeamMemberResultWithWarningDTO(BaseModel):
    result: AddTeamMemberResultDTO
    warning: Optional[str] = None


class TeamMemberRosterDTO(BaseModel):
    """Returned by list_team_members"""
    team_member_id: int
    team_id: int
    team_name: str
    student_id: int
    student_name: str
    amount_due: float = 0.0
    amount_paid: float = 0.0


class PayCompetitionFeeResponseDTO(BaseModel):
    """Returned by pay_competition_fee"""
    receipt_number: str
    payment_id: int
    amount: float
    amount_paid: float  # New running total after this payment
    amount_due: float  # For context


# Nested DTOs for the massive get_competition_summary

class TeamWithMembersDTO(BaseModel):
    team: TeamDTO
    members: list[TeamMemberDTO]


class CategoryWithTeamsDTO(BaseModel):
    category: str  # Category name from 3-table schema
    subcategory: Optional[str] = None
    teams: list[TeamWithMembersDTO]


class CompetitionSummaryDTO(BaseModel):
    """Returned by get_competition_summary"""
    competition: CompetitionDTO
    categories: list[CategoryWithTeamsDTO]


class TeamMemberWithNameDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member: TeamMemberDTO
    student_name: str


class CompetitionSummaryDataDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    competition: Optional[CompetitionDTO] = None
    teams: list[TeamDTO]
    members_by_team: dict[int, list[TeamMemberWithNameDTO]]


class CategorySubcategoryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    category: str
    subcategory: Optional[str] = None


class StudentMembershipEnrichedDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    membership: TeamMemberDTO
    team: TeamDTO
    competition: Optional[CompetitionDTO] = None
