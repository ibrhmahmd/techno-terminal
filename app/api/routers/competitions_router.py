"""
app/api/routers/competitions.py
───────────────────────────────
Competitions domain router (Stub Phase 5).

Prefix: /api/v1 (mounted in main.py)
Tag:    Competitions
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_competition_service, get_team_service
from app.modules.auth import User
from app.modules.competitions import CompetitionService, CompetitionDTO
from app.modules.competitions.services.team_service import TeamService

# Import actual schemas
from app.modules.competitions.schemas.competition_schemas import (
    CreateCompetitionInput,
    CompetitionCategoryDTO,
    AddCategoryInput,
)
from app.modules.competitions.schemas.team_schemas import (
    RegisterTeamInput,
    TeamRegistrationResultDTO,
    TeamWithMembersDTO,
)

router = APIRouter(tags=["Competitions"])


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
    response_model=ApiResponse[list[CompetitionCategoryDTO]],
    summary="List categories for a competition",
)
def list_categories(
    competition_id: int,
    _user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    cats = svc.list_categories(competition_id)
    return ApiResponse(data=[CompetitionCategoryDTO.model_validate(c) for c in cats])


@router.post(
    "/competitions/{competition_id}/categories",
    response_model=ApiResponse[CompetitionCategoryDTO],
    status_code=201,
    summary="Add a category to a competition",
)
def add_category(
    competition_id: int,
    body: AddCategoryInput,
    _user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    cat = svc.add_category(competition_id, body)
    return ApiResponse(
        data=CompetitionCategoryDTO.model_validate(cat),
        message="Category added successfully."
    )


@router.post(
    "/competitions/register",
    response_model=ApiResponse[TeamRegistrationResultDTO],
    status_code=201,
    summary="Register a team for a competition",
)
def register_team(
    body: RegisterTeamInput,
    _user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    result = svc.register_team(body)
    return ApiResponse(
        data=TeamRegistrationResultDTO.model_validate(result),
        message="Team registered successfully."
    )


@router.get(
    "/competitions/{competition_id}/categories/{category_id}/teams",
    response_model=ApiResponse[list[TeamWithMembersDTO]],
    summary="List teams in a competition category",
)
def list_teams_in_category(
    competition_id: int,
    category_id: int,
    _user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    # Pass arbitrary criteria to the existing search/list method
    teams = svc.get_teams_with_members(category_id)
    return ApiResponse(data=[TeamWithMembersDTO.model_validate(t) for t in teams])


@router.post(
    "/competitions/team-members/{team_member_id}/pay",
    response_model=ApiResponse[None],
    summary="Mark competition fee as paid (bypass Finance Desk)",
)
def mark_fee_as_paid(
    team_member_id: int,
    _user: User = Depends(require_admin),
    svc: TeamService = Depends(get_team_service),
):
    import app.modules.competitions.repositories.team_repository as team_repo
    from app.db.connection import get_session
    from app.modules.competitions.schemas.team_schemas import PayCompetitionFeeInput
    
    # Get team member details to construct proper input
    with get_session() as db:
        member = team_repo.get_team_member_by_id(db, team_member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        # Get student's parent for payment
        from app.modules.crm.models.student_models import Student
        student = db.get(Student, member.student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Construct proper input for service
        cmd = PayCompetitionFeeInput(
            team_id=member.team_id,
            student_id=member.student_id,
            parent_id=student.primary_parent_id or 0,
            received_by_user_id=_user.id if _user else 0
        )
    
    svc.pay_competition_fee(cmd)
    return ApiResponse(data=None, message="Fee marked as paid.")
