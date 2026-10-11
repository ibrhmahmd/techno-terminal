"""
app/modules/academics/api/groups_router.py
──────────────────────────────────────────
Groups core CRUD router.

Handles group creation, retrieval, update, status transitions, level progression,
and session listing. Uses GroupCoreService for state mutations and
GroupLifecycleService for compound operations.

Auth: GET = require_any, mutations = require_admin.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse
from app.modules.academics.api.schemas.group import (
    GroupPublic,
)
from app.modules.academics.api.schemas.session import SessionPublic, GenerateLevelSessionsRequest
from app.api.dependencies import (
    require_admin,
    require_any,
)
from app.modules.academics.api.deps import (
    get_group_service,
    get_session_service,
    get_lifecycle_service,
)
from app.modules.academics.schemas.group_schemas import ScheduleGroupInput, UpdateGroupDTO
from app.modules.academics.schemas.group_lifecycle_schemas import CreateGroupWithLevelDTO
from app.modules.academics.schemas.session_schemas import GenerateLevelSessionsInput
from app.modules.auth import User
from app.modules.academics.services.group_service import GroupCoreService
from app.modules.academics.services.session_service import SessionService
from app.modules.academics.services.group_lifecycle_service import GroupLifecycleService

router = APIRouter(tags=["Academics — Groups"])


# ── GET /academics/groups/{group_id} ─────────────────────────────────────────

@router.get(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Get group by ID",
)
def get_group(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupCoreService = Depends(get_group_service),
):
    group = svc.get_group_by_id(group_id)
    return ApiResponse(data=GroupPublic.model_validate(group))


# ── POST /academics/groups ────────────────────────────────────────────────────

@router.post(
    "/academics/groups",
    response_model=ApiResponse[GroupPublic],
    status_code=201,
    summary="Schedule a new group (creates Level 1 and sessions atomically)",
)
def create_group(
    body: ScheduleGroupInput,
    _user: User = Depends(require_admin),
    lifecycle_svc: GroupLifecycleService = Depends(get_lifecycle_service),
    svc: GroupCoreService = Depends(get_group_service),
):
    """
    Atomic operation: creates a new group, its Level 1, and the initial sessions
    all in a single transaction. Uses course.sessions_per_level for session count.
    """
    create_data = CreateGroupWithLevelDTO(group_input=body)
    result = lifecycle_svc.create_group_with_first_level(create_data)

    group = svc.get_group_by_id(result.group_id)

    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message=f"Group created with Level 1 and {result.sessions_count} sessions.",
    )


# ── PATCH /academics/groups/{group_id} ───────────────────────────────────────

@router.patch(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Update group metadata (name, capacity, schedule, etc.)",
)
def update_group(
    group_id: int,
    body: UpdateGroupDTO,
    _user: User = Depends(require_admin),
    svc: GroupCoreService = Depends(get_group_service),
):
    group = svc.update_group(group_id, body)
    return ApiResponse(data=GroupPublic.model_validate(group))


# ── PATCH /academics/groups/{group_id}/archive ───────────────────────────────

@router.patch(
    "/academics/groups/{group_id}/archive",
    response_model=ApiResponse[GroupPublic],
    summary="Archive a group (marks lifecycle as complete, status → 'completed')",
)
def archive_group(
    group_id: int,
    _user: User = Depends(require_admin),
    svc: GroupCoreService = Depends(get_group_service),
):
    """
    Archive a group that has finished its lifecycle.
    Status becomes 'completed'. Enrollments and history are preserved.
    This is different from DELETE which deactivates (suspends) the group.
    """
    group = svc.archive_group(group_id)
    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message="Group archived successfully.",
    )


# ── DELETE /academics/groups/{group_id} ──────────────────────────────────────

@router.delete(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Deactivate a group (suspend — status → 'inactive')",
)
def deactivate_group(
    group_id: int,
    _user: User = Depends(require_admin),
    svc: GroupCoreService = Depends(get_group_service),
):
    """
    Deactivate (suspend) a group. Status becomes 'inactive'.
    This is different from archiving — the group can be reactivated later.
    """
    group = svc.deactivate_group(group_id)
    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message="Group deactivated successfully.",
    )


# ── GET /academics/groups/{group_id}/sessions ─────────────────────────────────

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


# ── POST /academics/groups/{group_id}/generate-sessions ──────────────────────

@router.post(
    "/academics/groups/{group_id}/generate-sessions",
    response_model=ApiResponse[list[SessionPublic]],
    status_code=201,
    summary="Manually generate sessions for a specific level",
)
def generate_level_sessions(
    group_id: int,
    body: GenerateLevelSessionsRequest,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    data = GenerateLevelSessionsInput(
        group_id=group_id,
        level_number=body.level_number,
        start_date=body.start_date or date.today(),
    )
    sessions = svc.generate_level_sessions(data)
    return ApiResponse(
        data=[SessionPublic.model_validate(s) for s in sessions],
        message=f"Generated {len(sessions)} sessions for level {body.level_number}.",
    )
