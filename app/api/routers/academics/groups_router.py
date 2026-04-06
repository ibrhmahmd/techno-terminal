"""
app/api/routers/academics/groups.py
───────────────────────────────────
Groups router.

Endpoints for group management.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, Path

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.group import (
    GroupPublic,
    GroupListItem,
    EnrichedGroupPublic,
    ScheduleGroupLevelRequest,
    ProgressGroupLevelRequest,
)
from app.api.schemas.academics.session import (
    SessionPublic,
    GenerateLevelSessionsRequest,
)
from app.api.dependencies import (
    require_admin,
    require_any,
    get_group_service,
    get_session_service,
)
from app.modules.academics.schemas import ScheduleGroupInput, UpdateGroupDTO, ProgressGroupLevelResult
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


# get enriched groups (with instructor and course names) - MUST come before /{group_id}
@router.get(
    "/academics/groups/enriched",
    response_model=ApiResponse[list[EnrichedGroupPublic]],
    summary="Get all active groups with instructor and course names",
)
def list_enriched_groups(
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    groups = svc.get_all_active_groups_enriched()
    
    if not groups:
        return ApiResponse(data=[])
    
    return ApiResponse(
        data=[EnrichedGroupPublic.model_validate(g.model_dump(mode="json")) for g in groups]
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


# get enriched group by ID
@router.get(
    "/academics/groups/{group_id}/enriched",
    response_model=ApiResponse[EnrichedGroupPublic],
    summary="Get enriched group by ID",
)
def get_enriched_group(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):

    group = svc.get_enriched_group_by_id(group_id)

    if not group:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

    return ApiResponse(data=EnrichedGroupPublic.model_validate(group.model_dump(mode="json")))


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


# schedule group level
@router.post(
    "/academics/groups/{group_id}/schedule-level",
    response_model=ApiResponse[dict],
    status_code=201,
    summary="Schedule a new level for an existing group",
)
def schedule_group_level(
    group_id: int,
    body: ScheduleGroupLevelRequest,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    """
    Schedule a new level for an existing group.
    Creates GroupLevel record and generates 5 sessions.
    """
    from app.modules.academics.schemas import ScheduleGroupLevelInput

    data = ScheduleGroupLevelInput(
        group_id=group_id,
        level_number=body.level_number,
        instructor_id=body.instructor_id,
        price_override=body.price_override,
        start_date=body.start_date,
    )

    level, sessions = svc.schedule_group_level(data)

    return ApiResponse(
        data={
            "level_id": level.id,
            "level_number": level.level_number,
            "group_id": level.group_id,
            "sessions_created": len(sessions),
            "sessions": [{"id": s.id, "session_number": s.session_number, "date": s.session_date.isoformat()} for s in sessions],
        },
        message=f"Level {level.level_number} scheduled for group {group_id} with {len(sessions)} sessions.",
    )


# progress group level
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
    svc: GroupService = Depends(get_group_service),
):
    """
    Progress a group to the next level.
    Completes current level, creates new level, migrates enrollments.
    """
    from app.modules.academics.schemas import ProgressGroupLevelInput

    data = ProgressGroupLevelInput(
        group_id=group_id,
        price_override=body.price_override,
    )

    result = svc.progress_group_level(data)

    return ApiResponse(
        data=result,
        message=result.message,
    )


# delete group (soft delete)


@router.delete(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Soft delete a group (set inactive)",
)
def delete_group(
    group_id: int,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):

    group = svc.delete_group_by_id(group_id)

    if not group:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message="Group archived successfully.",
    )


# schedule group level


@router.post(
    "/academics/groups/{group_id}/schedule-level",
    response_model=ApiResponse[dict],
    status_code=201,
    summary="Schedule a new level for an existing group",
)
def schedule_group_level(
    group_id: int,
    body: ScheduleGroupLevelRequest,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    """
    Schedule a new level for an existing group.
    Creates GroupLevel record and generates 5 sessions.
    """
    from app.modules.academics.schemas import ScheduleGroupLevelInput

    data = ScheduleGroupLevelInput(
        group_id=group_id,
        level_number=body.level_number,
        instructor_id=body.instructor_id,
        price_override=body.price_override,
        start_date=body.start_date,
    )

    level, sessions = svc.schedule_group_level(data)

    return ApiResponse(
        data={
            "level_id": level.id,
            "level_number": level.level_number,
            "group_id": level.group_id,
            "sessions_created": len(sessions),
            "sessions": [{"id": s.id, "session_number": s.session_number, "date": s.session_date.isoformat()} for s in sessions],
        },
        message=f"Level {level.level_number} scheduled for group {group_id} with {len(sessions)} sessions.",
    )


# progress group level


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
    svc: GroupService = Depends(get_group_service),
):
    """
    Progress a group to the next level.
    Completes current level, creates new level, migrates enrollments.
    """
    from app.modules.academics.schemas import ProgressGroupLevelInput

    data = ProgressGroupLevelInput(
        group_id=group_id,
        price_override=body.price_override,
    )

    result = svc.progress_group_level(data)

    return ApiResponse(
        data=result,
        message=result.message,
    )


# generate level sessions manually


@router.post(
    "/academics/groups/{group_id}/generate-sessions",
    response_model=ApiResponse[list[SessionPublic]],
    status_code=201,
    summary="Generate sessions for a specific level",
)
def generate_level_sessions(
    group_id: int,
    body: GenerateLevelSessionsRequest,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):

    from app.modules.academics.schemas import GenerateLevelSessionsInput

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


# search groups


@router.get(
    "/academics/groups/search",
    response_model=PaginatedResponse[GroupListItem],
    summary="Search groups by name",
)
def search_groups(
    query: str = Query(..., min_length=2, description="Search query string"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    """Search groups by name using partial matching."""
    results, total = svc.search_groups(query, status, skip, limit)
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in results],
        total=total,
        skip=skip,
        limit=limit,
    )


# get groups by type


@router.get(
    "/academics/groups/by-type/{group_type}",
    response_model=PaginatedResponse[GroupListItem],
    summary="List groups by type",
)
def list_groups_by_type(
    group_type: str = Path(..., description="Group type to filter by"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    """Get groups filtered by type."""
    results, total = svc.get_groups_by_type(group_type, status, skip, limit)
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in results],
        total=total,
        skip=skip,
        limit=limit,
    )


# get groups by course
@router.get(
    "/academics/groups/by-course/{course_id}",
    response_model=PaginatedResponse[EnrichedGroupPublic],
    summary="Get all groups for a course",
)
def list_groups_by_course(
    course_id: int = Path(..., gt=0, description="Course ID"),
    include_inactive: bool = Query(False, description="Include inactive groups"),
    level_number: int | None = Query(None, gt=0, description="Filter by level number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    """Get all groups associated with a specific course."""
    results, total = svc.get_groups_by_course(
        course_id, include_inactive, level_number, skip, limit
    )
    return PaginatedResponse(
        data=[EnrichedGroupPublic.model_validate(g) for g in results],
        total=total,
        skip=skip,
        limit=limit,
    )
