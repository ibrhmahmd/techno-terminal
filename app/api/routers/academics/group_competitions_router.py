"""
app/api/routers/academics/group_competitions_router.py
──────────────────────────────────────────────────────
Router for group-centric competition APIs.

Covers:
- Listing a group's competition participations
- Listing and linking teams to a group
- Registering for and completing competitions
- Analytics

Auth: GET = require_any, mutations = require_admin.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.dependencies import (
    require_any,
    require_admin,
    get_group_competition_service,
    get_group_analytics_service,
)
from app.modules.auth import User
from app.modules.academics.group.competition.service import GroupCompetitionService
from app.modules.academics.group.analytics.service import GroupAnalyticsService
from app.modules.academics.group.analytics.schemas import GroupCompetitionHistoryResponseDTO
from app.api.schemas.academics.team import TeamPublic
from app.api.schemas.academics.competition import (
    GroupCompetitionPublic,
    TeamLinkResponse,
    CompetitionRegistrationResponse,
    CompetitionCompletionResponse,
    CompetitionWithdrawalResponse,
)

router = APIRouter(tags=["Academics — Group Competitions"])


# ── GET /academics/groups/{group_id}/competitions ─────────────────────────────

@router.get(
    "/academics/groups/{group_id}/competitions",
    response_model=ApiResponse[list[GroupCompetitionPublic]],
    summary="List competition participations for a group",
)
def list_group_competitions(
    group_id: int,
    is_active: bool | None = Query(None, description="Filter by active status"),
    _user: User = Depends(require_any),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """Returns all competition participations for a group."""
    participations = svc.get_group_competitions(group_id, is_active=is_active)
    return ApiResponse(
        data=[GroupCompetitionPublic.model_validate(p) for p in participations]
    )


# ── GET /academics/groups/{group_id}/teams ────────────────────────────────────

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
    """Returns paginated list of teams linked to a group."""
    teams, total = svc.get_teams_by_group(
        group_id=group_id,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(
        data=[TeamPublic.model_validate(t) for t in teams],
        total=total,
        skip=skip,
        limit=limit,
    )


# ── POST /academics/groups/{group_id}/teams/{team_id}/link ───────────────────

@router.post(
    "/academics/groups/{group_id}/teams/{team_id}/link",
    response_model=ApiResponse[TeamLinkResponse],
    summary="Link an existing team to a group",
)
def link_team_to_group(
    group_id: int,
    team_id: int,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """Link an existing team to a group. Requires admin privileges."""
    result = svc.link_existing_team(group_id, team_id)
    return ApiResponse(
        data=TeamLinkResponse.model_validate(result),
        message=f"Team {team_id} linked to group {group_id}",
    )


# ── POST /academics/groups/{group_id}/competitions/{competition_id}/register ──

@router.post(
    "/academics/groups/{group_id}/competitions/{competition_id}/register",
    response_model=ApiResponse[CompetitionRegistrationResponse],
    summary="Register a team for a competition",
)
def register_team_for_competition(
    group_id: int,
    competition_id: int,
    team_id: int,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """Register a team from this group for a competition. Requires admin privileges."""
    participation = svc.register_team(
        group_id=group_id,
        team_id=team_id,
        competition_id=competition_id,
    )
    return ApiResponse(
        data=CompetitionRegistrationResponse(
            participation_id=participation.id,
            group_id=participation.group_id,
            team_id=participation.team_id,
            competition_id=participation.competition_id,
            entered_at=participation.entered_at,
            is_active=participation.is_active,
            message="Team registered for competition successfully",
        ),
        message="Team registered for competition successfully",
    )


# ── PATCH /academics/groups/{group_id}/competitions/{participation_id}/complete

@router.patch(
    "/academics/groups/{group_id}/competitions/{participation_id}/complete",
    response_model=ApiResponse[CompetitionCompletionResponse],
    summary="Mark competition participation as completed",
)
def complete_competition_participation(
    group_id: int,
    participation_id: int,
    final_placement: int | None = None,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """Mark a competition participation as completed. Optionally record final placement."""
    participation = svc.complete_participation(participation_id, final_placement)
    return ApiResponse(
        data=CompetitionCompletionResponse(
            participation_id=participation.id,
            is_active=participation.is_active,
            left_at=participation.left_at,
            final_placement=participation.final_placement,
            message="Competition participation marked as completed",
        ),
        message="Competition participation marked as completed",
    )


# ── DELETE /academics/groups/{group_id}/competitions/{participation_id} ───────

@router.delete(
    "/academics/groups/{group_id}/competitions/{participation_id}",
    response_model=ApiResponse[CompetitionWithdrawalResponse],
    summary="Withdraw from competition",
)
def withdraw_from_competition(
    group_id: int,
    participation_id: int,
    reason: str | None = None,
    _user: User = Depends(require_admin),
    svc: GroupCompetitionService = Depends(get_group_competition_service),
):
    """Withdraw from a competition. Requires admin privileges."""
    result = svc.withdraw_from_competition(participation_id, reason)
    return ApiResponse(
        data=CompetitionWithdrawalResponse(
            participation_id=result.id,
            status=result.status,
            withdrawn_at=result.withdrawn_at,
            message="Successfully withdrew from competition.",
        ),
        message="Successfully withdrew from competition.",
    )


# ── GET /academics/groups/{group_id}/competitions/analytics ───────────────────

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
    Returns full competition participation history including team/category details,
    entry/exit dates, placement results, and active vs completed status.
    """
    history = svc.get_competition_history(group_id)
    return ApiResponse(data=history)
