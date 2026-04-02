"""
app/api/routers/academics/groups.py
───────────────────────────────────
Groups router.

Endpoints for group management.
"""
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.group import GroupPublic, GroupListItem
from app.api.schemas.academics.session import SessionPublic
from app.api.dependencies import require_admin, require_any, get_group_service, get_session_service
from app.modules.academics.schemas import ScheduleGroupInput, UpdateGroupDTO
from app.modules.auth import User
from app.modules.academics.services.group_service import GroupService
from app.modules.academics.services.session_service import SessionService

router = APIRouter(tags=["Academics — Groups"])

# list all active groups
@router.get(
    "/academics/groups",
    response_model=PaginatedResponse[GroupListItem],
    summary="List all active groups",
)
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    results = svc.get_all_active_groups()
    page = results[skip : skip + limit]
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in page],
        total=len(results),
        skip=skip,
        limit=limit,
    )


# get group by ID
@router.get(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Get group by ID",
)
def get_group(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    group = svc.get_group_by_id(group_id)
    return ApiResponse(data=GroupPublic.model_validate(group))


# create group
@router.post(
    "/academics/groups",
    response_model=ApiResponse[GroupPublic],
    status_code=201,
    summary="Schedule a new group",
)
def create_group(
    body: ScheduleGroupInput,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    # schedule_group returns (group, sessions) — sessions accessible via /groups/{id}/sessions
    group, _sessions = svc.schedule_group(body)
    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message="Group scheduled successfully.",
    )


# update group
@router.patch(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Update a group",
)
def update_group(
    group_id: int,
    body: UpdateGroupDTO,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    group = svc.update_group(group_id, body)
    return ApiResponse(data=GroupPublic.model_validate(group))


# list sessions for a group
@router.get(
    "/academics/groups/{group_id}/sessions",
    response_model=ApiResponse[list[SessionPublic]],
    summary="List sessions for a group (optionally filter by level)",
)
def list_group_sessions(
    group_id: int,
    level: int = Query(None, description="Filter to a specific level number"),
    _user: User = Depends(require_any),
    svc: SessionService = Depends(get_session_service),
):
    sessions = svc.list_group_sessions(group_id, level_number=level)
    return ApiResponse(data=[SessionPublic.model_validate(s) for s in sessions])


# progress group to the next level
@router.post(
    "/academics/groups/{group_id}/progress-level",
    response_model=ApiResponse[GroupPublic],
    summary="Progress group to the next level",
)
def progress_group_level(
    group_id: int,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    group = svc.progress_group_level(group_id)
    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message=f"Group progressed to level {group.level_number} successfully."
    )

