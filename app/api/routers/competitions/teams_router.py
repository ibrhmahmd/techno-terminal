"""
app/api/routers/competitions/teams_router.py
─────────────────────────────────────────
Teams router for 3-table schema.

Handles: Team lifecycle, members, payments, placement
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_team_service
from app.modules.auth import User
from app.modules.competitions.services.team_service import TeamService

from app.modules.competitions.schemas.team_schemas import (
    RegisterTeamInput,
    TeamRegistrationResultDTO,
    TeamWithMembersDTO,
    TeamDTO,
    PayCompetitionFeeInput,
    PayCompetitionFeeResponseDTO,
    StudentCompetitionDTO,
    AddTeamMemberResultDTO,
    TeamMemberRosterDTO,
)

router = APIRouter(tags=["Teams"])


# ── Helper DTOs ───────────────────────────────────────────────────────────────

class UpdateTeamInput(BaseModel):
    """Input for updating a team (partial updates supported)."""
    team_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    group_id: Optional[int] = None
    coach_id: Optional[int] = None
    fee: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=1000)


class PlacementUpdateInput(BaseModel):
    """Input for updating team placement."""
    placement_rank: int = Field(..., ge=1, description="Placement rank (1=1st place)")
    placement_label: Optional[str] = Field(None, max_length=100, description="Label like 'Gold' or '3rd Place'")


class AddTeamMemberInput(BaseModel):
    """Input for adding a member to an existing team."""
    student_id: int = Field(..., description="Student ID to add")


class TeamMemberListResponse(BaseModel):
    """Response for team member list."""
    team_id: int
    team_name: str
    members: list[TeamMemberRosterDTO]


class StudentCompetitionsResponse(BaseModel):
    """Response for student's competition history."""
    student_id: int
    competitions: list[StudentCompetitionDTO]


class DeletedTeamListResponse(BaseModel):
    """Response for listing deleted teams."""
    competition_id: Optional[int]
    teams: list[TeamDTO]
    total: int


# ── Team Endpoints ───────────────────────────────────────────────────────────

@router.get(
    "/teams",
    response_model=ApiResponse[list[TeamWithMembersDTO]],
    summary="List teams",
    description="List teams with optional filters for competition, category, and subcategory.",
)
def list_teams(
    competition_id: Optional[int] = Query(None, description="Filter by competition ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    include_members: bool = Query(True, description="Include team members in response"),
    current_user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """List teams with optional filters."""
    if competition_id is None:
        raise HTTPException(status_code=400, detail="competition_id is required")
    
    if include_members:
        teams = svc.get_teams_with_members(competition_id, category, subcategory)
    else:
        teams = svc.list_teams(competition_id, category, subcategory)
    
    return ApiResponse(data=teams)


@router.post(
    "/teams",
    response_model=ApiResponse[TeamRegistrationResultDTO],
    status_code=201,
    summary="Register a team",
    description="""
    Register a new team for a competition with members.
    
    Business Rules:
    - One student can only be in one team per competition
    - If category has subcategories, subcategory must be specified
    - Team name must be unique within the competition
    """,
    responses={
        400: {"description": "Validation error or business rule violation"},
        404: {"description": "Competition or student not found"},
        409: {"description": "Duplicate team name or student already enrolled"},
    },
)
def register_team(
    body: RegisterTeamInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Register a team for a competition."""
    result = svc.register_team(body, current_user_id=current_user.id)
    return ApiResponse(
        data=result,
        message="Team registered successfully."
    )


@router.get(
    "/teams/{team_id}",
    response_model=ApiResponse[TeamDTO],
    summary="Get team details",
    description="Retrieve full details for a specific team.",
    responses={
        404: {"description": "Team not found"},
    },
)
def get_team(
    team_id: int,
    current_user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """Get team by ID."""
    team = svc.update_team(team_id)  # Using update_team as a get since no direct get exists
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse(data=team)


@router.put(
    "/teams/{team_id}",
    response_model=ApiResponse[TeamDTO],
    summary="Update team (full)",
    description="Full update of team. All fields must be provided.",
    responses={
        404: {"description": "Team not found"},
    },
)
def update_team_full(
    team_id: int,
    body: UpdateTeamInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Full update of team."""
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    
    team = svc.update_team(team_id, **update_data)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return ApiResponse(data=team, message="Team updated successfully.")


@router.patch(
    "/teams/{team_id}",
    response_model=ApiResponse[TeamDTO],
    summary="Update team (partial)",
    description="Partial update of team. Only provided fields are updated.",
    responses={
        404: {"description": "Team not found"},
    },
)
def update_team_partial(
    team_id: int,
    body: UpdateTeamInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Partial update of team."""
    return update_team_full(team_id, body, current_user, svc)


@router.delete(
    "/teams/{team_id}",
    response_model=ApiResponse[bool],
    summary="Delete team",
    description="""
    Soft delete a team. Cannot delete if members have paid fees.
    
    Business Rules:
    - Cannot delete team with paid members
    """,
    responses={
        404: {"description": "Team not found"},
        409: {"description": "Cannot delete: team has paid members"},
    },
)
def delete_team(
    team_id: int,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Soft delete a team."""
    result = svc.delete_team(team_id, deleted_by=current_user.id)
    return ApiResponse(data=result, message="Team deleted successfully.")


@router.post(
    "/teams/{team_id}/restore",
    response_model=ApiResponse[bool],
    summary="Restore team",
    description="Restore a soft-deleted team.",
    responses={
        404: {"description": "Team not found"},
    },
)
def restore_team(
    team_id: int,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Restore a soft-deleted team."""
    result = svc.restore_team(team_id)
    return ApiResponse(data=result, message="Team restored successfully.")


@router.get(
    "/teams/deleted",
    response_model=ApiResponse[DeletedTeamListResponse],
    summary="List deleted teams",
    description="List all soft-deleted teams, optionally filtered by competition.",
)
def list_deleted_teams(
    competition_id: Optional[int] = Query(None, description="Filter by competition ID"),
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """List soft-deleted teams."""
    teams = svc.list_deleted_teams(competition_id)
    return ApiResponse(data=DeletedTeamListResponse(
        competition_id=competition_id,
        teams=teams,
        total=len(teams),
    ))


# ── Team Members Endpoints ────────────────────────────────────────────────────

@router.get(
    "/teams/{team_id}/members",
    response_model=ApiResponse[TeamMemberListResponse],
    summary="List team members",
    description="Get all members of a team with their payment status.",
    responses={
        404: {"description": "Team not found"},
    },
)
def list_team_members(
    team_id: int,
    current_user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """List all members of a team."""
    members = svc.list_team_members(team_id)
    
    # Get team name from first member's team or fetch separately
    team_name = "Unknown"
    if members and members[0]:
        # Try to get team info
        team = svc.update_team(team_id)
        if team:
            team_name = team.team_name
    
    return ApiResponse(data=TeamMemberListResponse(
        team_id=team_id,
        team_name=team_name,
        members=members,
    ))


@router.post(
    "/teams/{team_id}/members",
    response_model=ApiResponse[AddTeamMemberResultDTO],
    status_code=201,
    summary="Add team member",
    description="""
    Add a student to an existing team.
    
    Business Rules:
    - Student cannot already be in another team for this competition
    - Student must be active
    """,
    responses={
        400: {"description": "Business rule violation"},
        404: {"description": "Team or student not found"},
        409: {"description": "Student already enrolled in this competition or team"},
    },
)
def add_team_member(
    team_id: int,
    body: AddTeamMemberInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Add a member to an existing team."""
    result = svc.add_team_member_to_existing(
        team_id=team_id,
        student_id=body.student_id,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=result, message="Member added successfully.")


@router.delete(
    "/teams/{team_id}/members/{student_id}",
    response_model=ApiResponse[bool],
    summary="Remove team member",
    description="""
    Remove a student from a team.
    
    Business Rules:
    - Cannot remove a member who has already paid
    """,
    responses={
        400: {"description": "Cannot remove paid member"},
        404: {"description": "Team or member not found"},
    },
)
def remove_team_member(
    team_id: int,
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Remove a member from a team."""
    result = svc.remove_team_member(team_id, student_id)
    return ApiResponse(data=result, message="Member removed successfully.")


@router.post(
    "/teams/{team_id}/members/{student_id}/pay",
    response_model=ApiResponse[PayCompetitionFeeResponseDTO],
    summary="Pay competition fee",
    description="""
    Process competition fee payment for a team member.
    Creates a receipt and marks fee as paid.
    
    Business Rules:
    - Cannot pay if fee already paid
    - Payment is atomic (receipt + fee marking)
    - On failure, payment is automatically refunded
    """,
    responses={
        400: {"description": "Fee already paid or invalid input"},
        404: {"description": "Team or member not found"},
    },
)
def pay_competition_fee(
    team_id: int,
    student_id: int,
    parent_id: Optional[int] = Query(None, description="Parent ID for payment attribution"),
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Process competition fee payment for a team member."""
    cmd = PayCompetitionFeeInput(
        team_id=team_id,
        student_id=student_id,
        parent_id=parent_id,
        received_by_user_id=current_user.id,
    )
    
    result = svc.pay_competition_fee(cmd)
    return ApiResponse(data=result, message="Payment processed successfully.")


@router.patch(
    "/teams/{team_id}/placement",
    response_model=ApiResponse[TeamDTO],
    summary="Update team placement",
    description="""
    Update team placement after competition.
    Can only be set after competition date has passed.
    
    Business Rules:
    - Cannot set placement before competition date
    """,
    responses={
        400: {"description": "Competition date has not passed"},
        404: {"description": "Team not found"},
    },
)
def update_team_placement(
    team_id: int,
    body: PlacementUpdateInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Update team placement."""
    result = svc.update_placement(
        team_id=team_id,
        placement_rank=body.placement_rank,
        placement_label=body.placement_label,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=result, message="Placement updated successfully.")


# ── Student Context Endpoints ─────────────────────────────────────────────────

@router.get(
    "/students/{student_id}/competitions",
    response_model=ApiResponse[StudentCompetitionsResponse],
    summary="Get student's competitions",
    description="Get all competitions a student is registered in with their team details.",
    responses={
        404: {"description": "Student not found"},
    },
)
def get_student_competitions(
    student_id: int,
    current_user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """Get all competitions for a student."""
    competitions = svc.get_student_competitions(student_id)
    return ApiResponse(data=StudentCompetitionsResponse(
        student_id=student_id,
        competitions=competitions,
    ))
