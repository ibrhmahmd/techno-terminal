"""
app/api/routers/competitions/teams_router.py
─────────────────────────────────────────
Teams router for 3-table schema.

Handles: Team lifecycle, members, payments, placement
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse
from app.api.schemas.competitions.team_schemas import (
    UpdateTeamInput,
    PlacementUpdateInput,
    TeamMemberListResponse,
    StudentCompetitionsResponse,
    RefundCompetitionFeeBody,
)
from app.api.dependencies import require_any, require_admin, get_team_service, require_coach_or_admin
from app.modules.auth import User
from app.modules.competitions.services.team_service import TeamService

from app.modules.competitions.schemas.team_schemas import (
    RegisterTeamInput,
    AddTeamMemberInput,
    TeamRegistrationResultDTO,
    TeamWithMembersDTO,
    TeamDTO,
    PayCompetitionFeeInput,
    PayCompetitionFeeResponseDTO,
    AddTeamMemberResultDTO,
    TeamMemberRosterDTO,
)

router = APIRouter(tags=["Teams"])


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
    """List teams with optional filters. Coaches see only their own teams."""
    if competition_id is None:
        raise HTTPException(status_code=400, detail="competition_id is required")

    if not current_user.is_admin and current_user.employee_id:
        teams = svc.list_teams_for_coach(competition_id, current_user.employee_id, category, subcategory)
        if include_members:
            result = []
            for team in teams:
                members = svc.get_team_members_for_team(team.id)
                result.append(
                    TeamWithMembersDTO(
                        team=TeamDTO.model_validate(team),
                        members=[TeamMemberDTO.model_validate(m) for m in members]
                    )
                )
            return ApiResponse(data=result)
        return ApiResponse(data=[TeamDTO.model_validate(t) for t in teams])

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
    current_user: User = Depends(require_coach_or_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Get team by ID."""
    team = svc.get_team_by_id(team_id)
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
    summary="Hard delete team",
    description="""
    Permanently delete a team. Cannot delete if members have paid fees.
    
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
    """Hard delete a team."""
    result = svc.delete_team(team_id)
    return ApiResponse(data=result, message="Team deleted successfully.")


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
    current_user: User = Depends(require_coach_or_admin),
    svc: TeamService = Depends(get_team_service),
):
    """List all members of a team."""
    members = svc.list_team_members(team_id)
    team_name = members[0].team_name if members else "Unknown"
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
        amount_due=body.amount_due,
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
    Creates a receipt and records the payment. Supports partial payments.
    
    Business Rules:
    - Payment amount must be > 0
    - Payment is atomic (receipt + fee recording)
    - On failure, payment is automatically refunded
    """,
    responses={
        400: {"description": "Invalid payment amount or business rule violation"},
        404: {"description": "Team or member not found"},
    },
)
def pay_competition_fee(
    team_id: int,
    student_id: int,
    body: PayCompetitionFeeInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Process competition fee payment for a team member."""
    cmd = PayCompetitionFeeInput(
        team_id=team_id,
        student_id=student_id,
        amount=body.amount,
        parent_id=body.parent_id,
        received_by_user_id=current_user.id,
    )
    
    result = svc.pay_competition_fee(cmd)
    return ApiResponse(data=result, message="Payment processed successfully.")


@router.post(
    "/teams/{team_id}/members/{student_id}/refund",
    response_model=ApiResponse[bool],
    summary="Refund competition fee",
    description="""
    Refund a competition fee payment for a team member.
    Creates a refund receipt and decreases amount_paid.
    
    Business Rules:
    - Refund amount must be > 0 and <= current amount_paid
    - Refund is atomic (receipt + fee adjustment)
    - On failure, entire operation rolls back
    - Admin only
    """,
    responses={
        400: {"description": "Invalid refund amount or business rule violation"},
        404: {"description": "Team or member not found"},
    },
)
def refund_competition_fee(
    team_id: int,
    student_id: int,
    body: RefundCompetitionFeeBody,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Refund a competition fee payment for a team member."""
    member = svc.get_team_member(team_id, student_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found.")
    if body.amount > member.amount_paid:
        raise HTTPException(
            status_code=400,
            detail=f"Refund amount ({body.amount}) exceeds amount paid ({member.amount_paid}).",
        )
    svc.refund_competition_fee(team_member_id=member.id, amount=body.amount)
    return ApiResponse(data=True, message=f"Refund of {body.amount} processed successfully.")


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
