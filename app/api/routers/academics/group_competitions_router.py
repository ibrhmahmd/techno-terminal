"""
app/api/routers/academics/group_competitions.py
──────────────────────────────────────────────
Router for group-centric competition APIs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.dependencies import require_any, require_admin, get_group_competition_service, get_team_service, get_group_analytics_service
from app.modules.auth import User
from app.modules.academics.services.group_competition_service import GroupCompetitionService
from app.modules.academics.services.group_analytics_service import GroupAnalyticsService
from app.modules.competitions.services.team_service import TeamService
from app.api.schemas.academics.group_analytics import GroupCompetitionHistoryResponseDTO
from app.api.schemas.academics.team import TeamPublic

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
    response_model=PaginatedResponse[TeamPublic],
    summary="List teams linked to a group",
)
def list_group_teams(
    group_id: int,
    include_inactive: bool = Query(False, description="Include inactive/deleted teams"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    _user: User = Depends(require_any),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Returns paginated list of teams linked to a group.
    
    Query params:
    - include_inactive: Include teams marked as deleted if True
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    teams, total = svc.get_teams_by_group(
        group_id=group_id,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit
    )
    
    return PaginatedResponse(
        data=[TeamPublic.model_validate(t) for t in teams],
        total=total,
        skip=skip,
        limit=limit,
    )


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
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Register a team from this group for a competition.
    Requires admin privileges.
    
    Args:
        team_id: The team to register
    """
    try:
        participation = svc.register_team(
            group_id=group_id,
            team_id=team_id,
            competition_id=competition_id,
        )
        return ApiResponse(
            data={
                "participation_id": participation.id,
                "group_id": participation.group_id,
                "team_id": participation.team_id,
                "competition_id": participation.competition_id,
                "category": participation.team.category if participation.team else None,
                "subcategory": participation.team.subcategory if participation.team else None,
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


@router.delete(
    "/academics/groups/{group_id}/competitions/{participation_id}",
    response_model=ApiResponse[dict],
    summary="Withdraw from competition",
)
def withdraw_from_competition(
    group_id: int,
    participation_id: int,
    reason: str | None = None,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """
    Withdraw from a competition.
    Requires admin privileges.
    """
    try:
        result = svc.withdraw_from_competition(participation_id, reason)
        return ApiResponse(
            data={
                "participation_id": result["id"],
                "status": result["status"],
                "withdrawn_at": result["withdrawn_at"],
            },
            message="Successfully withdrew from competition.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/academics/groups/{group_id}/competitions/analytics",
    response_model=ApiResponse[GroupCompetitionHistoryResponseDTO],
    summary="Get full competition participation history",
)
def get_group_competitions_analytics(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupAnalyticsService = Depends(get_group_analytics_service),
):
    """
    Returns full competition participation history including:
    - All competition participations for the group
    - Team and category details
    - Entry/exit dates and placement results
    - Active vs completed status
    """
    history = svc.get_competition_history(group_id)
    return ApiResponse(data=history)
