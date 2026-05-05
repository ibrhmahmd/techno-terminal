"""
app/api/routers/academics/groups_router.py
──────────────────────────────────────────
Groups core CRUD router.

Handles group creation, retrieval, update, status transitions, level progression,
and session listing. Uses GroupCoreService for state mutations and
GroupLifecycleService for compound operations.

Auth: GET = require_any, mutations = require_admin.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.group import (
    GroupPublic,
    GroupListItem,
    ProgressGroupLevelRequest,
    ProgressGroupLevelResult,
)
from app.api.schemas.academics.session import SessionPublic, GenerateLevelSessionsRequest
from app.api.dependencies import (
    require_admin,
    require_any,
    get_group_service,
    get_session_service,
)
from app.modules.academics.group.core.schemas import ScheduleGroupInput, UpdateGroupDTO
from app.modules.auth import User
from app.modules.academics.group.core.service import GroupCoreService
from app.modules.academics.session.service import SessionService
from app.modules.academics.group.lifecycle.service import GroupLifecycleService

router = APIRouter(tags=["Academics — Groups"])


def get_lifecycle_service() -> GroupLifecycleService:
    """Dependency provider for GroupLifecycleService."""
    return GroupLifecycleService()


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
):
    """
    Atomic operation: creates a new group, its Level 1, and the initial sessions
    all in a single transaction. Uses course.sessions_per_level for session count.
    """
    from app.modules.academics.group.lifecycle.schemas import CreateGroupWithLevelDTO
    from app.modules.academics.models import Group
    from app.db.connection import get_session

    create_data = CreateGroupWithLevelDTO(group_input=body)
    result = lifecycle_svc.create_group_with_first_level(create_data)

    with get_session() as session:
        group = session.get(Group, result.group_id)

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


# ── POST /academics/groups/{group_id}/progress-level ─────────────────────────

@router.post(
    "/academics/groups/{group_id}/progress-level",
    response_model=ApiResponse[ProgressGroupLevelResult],
    status_code=200,
    summary="Progress group to next level",
)
def progress_group_level(
    group_id: int,
    body: ProgressGroupLevelRequest,
    _user: User = Depends(require_admin),
    lifecycle_svc: GroupLifecycleService = Depends(get_lifecycle_service),
):
    """
    Progress a group to the next level.
    Completes current level, creates new level, migrates enrollments,
    generates sessions, and logs activity for each affected student.
    """
    from app.modules.academics.group.lifecycle.schemas import ProgressLevelDTO

    data = ProgressLevelDTO(
        group_id=group_id,
        price_override=body.price_override,
        auto_migrate_enrollments=body.auto_migrate_enrollments,
        target_level=body.target_level,
        complete_current_level=body.complete_current_level,
        instructor_id=body.instructor_id,
        session_start_date=body.session_start_date,
        course_id=body.course_id,
        group_name=body.group_name,
    )

    try:
        result = lifecycle_svc.progress_to_next_level(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(
        data=ProgressGroupLevelResult(
            old_level_number=result.old_level_number,
            new_level_number=result.new_level_number,
            enrollments_migrated=result.enrollments_migrated,
            sessions_created=result.sessions_created,
            message=result.message,
        ),
        message=result.message,
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
    from app.modules.academics.session.schemas import GenerateLevelSessionsInput

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
