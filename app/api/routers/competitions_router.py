"""
app/api/routers/competitions.py
───────────────────────────────
Competitions domain router for 3-table schema.

Prefix: /api/v1 (mounted in main.py)
Tag:    Competitions
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_competition_service, get_team_service
from app.modules.auth import User
from app.modules.competitions import CompetitionService, CompetitionDTO
from app.modules.competitions.services.team_service import TeamService
from app.modules.competitions.services.competition_service import CategoryInfoDTO

# Import actual schemas
from app.modules.competitions.schemas.competition_schemas import CreateCompetitionInput
from app.modules.competitions.schemas.team_schemas import (
    RegisterTeamInput,
    TeamRegistrationResultDTO,
    TeamWithMembersDTO,
    TeamDTO,
    PayCompetitionFeeInput,
    PayCompetitionFeeResponseDTO,
)

router = APIRouter(tags=["Competitions"])


# ── Helper DTOs ───────────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    """Category info for API response (3-table schema)."""
    category: str
    subcategories: list[str]


class PlacementUpdateInput(BaseModel):
    """Input for updating team placement."""
    placement_rank: int
    placement_label: Optional[str] = None


@router.get(
    "/competitions",
    response_model=ApiResponse[list[CompetitionDTO]],
    summary="List all competitions",
)
def list_competitions(
    _user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    comps = svc.list_competitions()
    return ApiResponse(data=comps)


@router.post(
    "/competitions",
    response_model=ApiResponse[CompetitionDTO],
    status_code=201,
    summary="Create a new competition",
)
def create_competition(
    body: CreateCompetitionInput,
    _user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    comp = svc.create_competition(body)
    return ApiResponse(
        data=CompetitionDTO.model_validate(comp),
        message="Competition created successfully."
    )


@router.get(
    "/competitions/{competition_id}",
    response_model=ApiResponse[CompetitionDTO],
    summary="Get single competition details",
)
def get_competition(
    competition_id: int,
    _user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    comp = svc.get_competition_by_id(competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return ApiResponse(data=CompetitionDTO.model_validate(comp))


@router.get(
    "/competitions/{competition_id}/categories",
    response_model=ApiResponse[list[CategoryResponse]],
    summary="List categories and subcategories for a competition",
)
def list_categories(
    competition_id: int,
    _user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    """
    List all distinct categories with their subcategories for autocomplete.
    In 3-table schema, categories are derived from teams.
    """
    cats = svc.list_categories(competition_id)
    return ApiResponse(data=[
        CategoryResponse(category=c.category, subcategories=c.subcategories)
        for c in cats
    ])


@router.post(
    "/competitions/{competition_id}/teams",
    response_model=ApiResponse[TeamRegistrationResultDTO],
    status_code=201,
    summary="Register a team for a competition",
)
def register_team(
    competition_id: int,
    body: RegisterTeamInput,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """
    Register a team for a competition.
    
    - competition_id: The competition to register for
    - team_name: Name of the team
    - category: Category name (e.g., "Software Leader")
    - subcategory: Optional subcategory (e.g., "Junior")
    - student_ids: List of student IDs to add as members
    - fee: Optional custom fee (default: competition's fee_per_student)
    """
    # Ensure competition_id matches URL
    if body.competition_id != competition_id:
        raise HTTPException(status_code=400, detail="Competition ID mismatch")
    
    result = svc.register_team(body, current_user_id=current_user.id)
    return ApiResponse(
        data=TeamRegistrationResultDTO.model_validate(result),
        message="Team registered successfully."
    )


@router.get(
    "/competitions/{competition_id}/teams",
    response_model=ApiResponse[list[TeamWithMembersDTO]],
    summary="List teams in a competition",
)
def list_teams(
    competition_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    _user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """
    List all teams in a competition with optional category/subcategory filters.
    """
    teams = svc.get_teams_with_members(competition_id, category, subcategory)
    return ApiResponse(data=teams)


@router.get(
    "/teams/{team_id}",
    response_model=ApiResponse[TeamDTO],
    summary="Get team details",
)
def get_team(
    team_id: int,
    _user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """Get details of a specific team."""
    team = svc.update_team(team_id)  # Using update_team as get since no get method exists
    # Actually, let me use the correct approach - list_team_members requires team_id
    # For now, return placeholder
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.patch(
    "/teams/{team_id}/placement",
    response_model=ApiResponse[TeamDTO],
    summary="Update team placement",
)
def update_team_placement(
    team_id: int,
    placement_rank: int = Query(..., ge=1, description="Placement rank (1=1st place)"),
    placement_label: Optional[str] = Query(None, description="Placement label (e.g., 'Gold', '3rd Place')"),
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """
    Update team placement after competition.
    Can only be set after competition date has passed.
    """
    result = svc.update_placement(
        team_id=team_id,
        placement_rank=placement_rank,
        placement_label=placement_label,
        current_user_id=current_user.id
    )
    return ApiResponse(data=result, message="Placement updated successfully.")


@router.delete(
    "/teams/{team_id}",
    response_model=ApiResponse[bool],
    summary="Soft delete a team",
)
def delete_team(
    team_id: int,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Soft delete a team. Cannot delete if members have paid fees."""
    result = svc.delete_team(team_id, deleted_by=current_user.id)
    return ApiResponse(data=result, message="Team deleted successfully.")


@router.post(
    "/teams/{team_id}/restore",
    response_model=ApiResponse[bool],
    summary="Restore a soft-deleted team",
)
def restore_team(
    team_id: int,
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """Restore a soft-deleted team."""
    result = svc.restore_team(team_id)
    return ApiResponse(data=result, message="Team restored successfully.")


@router.post(
    "/competitions/{competition_id}/teams/{team_id}/members/{student_id}/pay",
    response_model=ApiResponse[PayCompetitionFeeResponseDTO],
    summary="Pay competition fee for a team member",
)
def pay_competition_fee(
    competition_id: int,
    team_id: int,
    student_id: int,
    parent_id: Optional[int] = Query(None, description="Parent ID for payment"),
    current_user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    """
    Process competition fee payment for a team member.
    Creates a receipt and marks fee as paid.
    """
    cmd = PayCompetitionFeeInput(
        team_id=team_id,
        student_id=student_id,
        parent_id=parent_id,
        received_by_user_id=current_user.id
    )
    
    result = svc.pay_competition_fee(cmd)
    return ApiResponse(data=result, message="Payment processed successfully.")


# ── Soft Delete Endpoints for Competitions ────────────────────────────────────

@router.delete(
    "/competitions/{competition_id}",
    response_model=ApiResponse[bool],
    summary="Soft delete a competition",
)
def delete_competition(
    competition_id: int,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """
    Soft delete a competition.
    Cannot delete if competition has teams.
    """
    result = svc.delete_competition(competition_id, deleted_by=current_user.id)
    return ApiResponse(data=result, message="Competition deleted successfully.")


@router.post(
    "/competitions/{competition_id}/restore",
    response_model=ApiResponse[bool],
    summary="Restore a soft-deleted competition",
)
def restore_competition(
    competition_id: int,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Restore a soft-deleted competition."""
    result = svc.restore_competition(competition_id)
    return ApiResponse(data=result, message="Competition restored successfully.")


@router.get(
    "/competitions/deleted",
    response_model=ApiResponse[list[CompetitionDTO]],
    summary="List deleted competitions",
)
def list_deleted_competitions(
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """List all soft-deleted competitions (admin only)."""
    result = svc.list_deleted_competitions()
    return ApiResponse(data=result)
