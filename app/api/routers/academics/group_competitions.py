"""
app/api/routers/academics/group_competitions.py
──────────────────────────────────────────────
Router for group-centric competition APIs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_group_competition_service, get_team_service
from app.modules.auth import User
from app.modules.academics.services.group_competition_service import GroupCompetitionService
from app.modules.competitions.services.team_service import TeamService

router = APIRouter(tags=["Academics — Group Competitions"])


@router.get(
    "/academics/groups/{group_id}/competitions",
    response_model=ApiResponse[list[dict]],
    summary="List competition participations for a group",
)
def list_group_competitions(
    group_id: int,
    is_active: bool | None = Query(None, description="Filter by active status"),
    _user: User = Depends(require_any),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Returns all competition participations for a group.
    
    Query params:
    - is_active: Filter by active status (True/False/None for all)
    """
    participations = svc.get_group_competitions(group_id, is_active=is_active)
    return ApiResponse(data=participations)


@router.get(
    "/academics/groups/{group_id}/teams",
    response_model=ApiResponse[list[dict]],
    summary="List teams linked to a group",
)
def list_group_teams(
    group_id: int,
    include_inactive: bool = Query(False, description="Include inactive/deleted teams"),
    _user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
):
    """
    Returns all teams linked to a group.
    
    Query params:
    - include_inactive: Include teams marked as deleted if True
    """
    from app.db.connection import get_session
    from sqlmodel import select
    from app.modules.competitions.models.team_models import Team
    
    with get_session() as session:
        stmt = select(Team).where(Team.group_id == group_id)
        if not include_inactive:
            stmt = stmt.where(Team.is_deleted == False)
        
        teams = session.exec(stmt).all()
        return ApiResponse(data=[
            {
                "id": t.id,
                "team_name": t.team_name,
                "group_id": t.group_id,
                "coach_id": t.coach_id,
                "created_at": t.created_at,
                "is_deleted": t.is_deleted,
            }
            for t in teams
        ])


@router.post(
    "/academics/groups/{group_id}/teams/{team_id}/link",
    response_model=ApiResponse[dict],
    summary="Link an existing team to a group",
)
def link_team_to_group(
    group_id: int,
    team_id: int,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Link an existing team to a group.
    Requires admin privileges.
    """
    try:
        result = svc.link_existing_team(group_id, team_id)
        return ApiResponse(
            data=result,
            message=f"Team {team_id} linked to group {group_id}",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/academics/groups/{group_id}/competitions/{competition_id}/register",
    response_model=ApiResponse[dict],
    summary="Register a team for a competition",
)
def register_team_for_competition(
    group_id: int,
    competition_id: int,
    team_id: int,
    category_id: int | None = None,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Register a team from this group for a competition.
    Requires admin privileges.
    
    Args:
        team_id: The team to register
        category_id: Optional competition category
    """
    try:
        participation = svc.register_team(
            group_id=group_id,
            team_id=team_id,
            competition_id=competition_id,
            category_id=category_id,
        )
        return ApiResponse(
            data={
                "participation_id": participation.id,
                "group_id": participation.group_id,
                "team_id": participation.team_id,
                "competition_id": participation.competition_id,
                "entered_at": participation.entered_at,
                "is_active": participation.is_active,
            },
            message="Team registered for competition successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/academics/groups/{group_id}/competitions/{participation_id}/complete",
    response_model=ApiResponse[dict],
    summary="Mark competition participation as completed",
)
def complete_competition_participation(
    group_id: int,
    participation_id: int,
    final_placement: int | None = None,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Mark a competition participation as completed.
    Optionally record final placement/ranking.
    """
    try:
        participation = svc.complete_participation(participation_id, final_placement)
        return ApiResponse(
            data={
                "participation_id": participation.id,
                "is_active": participation.is_active,
                "left_at": participation.left_at,
                "final_placement": participation.final_placement,
            },
            message="Competition participation marked as completed",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
