"""
app/api/routers/academics/group_lifecycle.py
───────────────────────────────────────────
Router for group lifecycle and history endpoints.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.dependencies import require_any, require_admin, get_group_service, get_group_history_service, get_group_level_service, get_group_analytics_service
from app.modules.auth import User
from app.modules.academics.services.group_service import GroupService
from app.modules.academics.services.group_history_service import GroupHistoryService
from app.modules.academics.services.group_level_service import GroupLevelService
from app.modules.academics.services.group_analytics_service import GroupAnalyticsService
from app.api.schemas.academics.group_analytics import (
    GroupLevelHistoryResponseDTO,
    GroupEnrollmentHistoryResponseDTO,
    GroupInstructorHistoryResponseDTO,
)
from app.api.schemas.academics.group_lifecycle import CancelLevelInput
from app.api.schemas.academics.group_level import GroupLevelPublic

router = APIRouter(tags=["Academics — Group Lifecycle"])


@router.get(
    "/academics/groups/{group_id}/history",
    response_model=ApiResponse[dict],
    
    summary="Get full lifecycle history for a group",
)
def get_group_lifecycle_history(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupHistoryService = Depends(get_group_history_service),
):
    """
    Returns complete lifecycle data for a group including:
    - Levels timeline (chronological)
    - Course assignment history
    - Enrollment transitions
    """
    history = svc.get_full_lifecycle(group_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/levels",
    response_model=PaginatedResponse[GroupLevelPublic],
    summary="List all level snapshots for a group",
)
def list_group_levels(
    group_id: int,
    status: str | None = None,
    include_inactive: bool = False,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    _user: User = Depends(require_any),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Returns paginated level snapshots for a group.
    Query params:
    - status: Filter by status (active, completed, cancelled)
    - include_inactive: Include inactive levels if True
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    levels, total = svc.get_paginated_levels(
        group_id=group_id,
        status=status,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit
    )
    
    return PaginatedResponse(
        data=[GroupLevelPublic.model_validate(l) for l in levels],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/academics/groups/{group_id}/levels/{level_number}",
    response_model=ApiResponse[GroupLevelPublic],
    summary="Get specific level details",
)
def get_group_level(
    group_id: int,
    level_number: int,
    _user: User = Depends(require_any),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Returns detailed level information including course and instructor names.
    """
    level = svc.get_level_by_number(group_id, level_number)
    return ApiResponse(data=GroupLevelPublic.model_validate(level))


@router.post(
    "/academics/groups/{group_id}/levels/{level_number}/complete",
    response_model=ApiResponse[dict],
    summary="Complete a level and progress to next",
)
def complete_group_level(
    group_id: int,
    level_number: int,
    _user: User = Depends(require_admin),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Mark a level as completed and create next level snapshot.
    Requires admin privileges.
    """
    try:
        completed, new_level = svc.complete_current_level(group_id)
        return ApiResponse(
            data={
                "completed_level": {
                    "id": completed.id,
                    "level_number": completed.level_number,
                    "status": completed.status,
                },
                "new_level": {
                    "id": new_level.id,
                    "level_number": new_level.level_number,
                    "status": new_level.status,
                },
            },
            message=f"Group progressed from level {completed.level_number} to level {new_level.level_number}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/academics/groups/{group_id}/levels/{level_number}/cancel",
    response_model=ApiResponse[dict],
    summary="Cancel a group level",
)
def cancel_group_level_endpoint(
    group_id: int,
    level_number: int,
    body: CancelLevelInput = Body(...),
    _user: User = Depends(require_admin),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Cancel a group level that hasn't been completed yet.
    Requires admin privileges.
    """
    try:
        cancelled_level = svc.cancel_level(group_id, level_number, body.reason)
        return ApiResponse(
            data={
                "level_id": cancelled_level.id,
                "level_number": cancelled_level.level_number,
                "status": cancelled_level.status,
            },
            message=f"Level {level_number} cancelled successfully.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/academics/groups/{group_id}/courses/history",
    response_model=ApiResponse[list[dict]],
    summary="Get course assignment history",
)
def get_group_course_history(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupHistoryService = Depends(get_group_history_service),
):
    """Returns chronological course assignment history for a group."""
    history = svc.get_course_assignments(group_id)
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/enrollments/history",
    response_model=ApiResponse[list[dict]],
    summary="Get enrollment level transitions",
)
def get_group_enrollment_history(
    group_id: int,
    student_id: int | None = None,
    _user: User = Depends(require_any),
    svc: GroupHistoryService = Depends(get_group_history_service),
):
    """
    Returns enrollment level transitions for a group.
    Optionally filter by specific student.
    """
    transitions = svc.get_enrollment_transitions(group_id, student_id)
    return ApiResponse(data=transitions)


# ═══════════════════════════════════════════════════════════════════════════════
# NEW GROUP ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/academics/groups/{group_id}/levels/analytics",
    response_model=ApiResponse[GroupLevelHistoryResponseDTO],
    summary="Get level progression history with student counts",
)
def get_group_levels_analytics(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupAnalyticsService = Depends(get_group_analytics_service),
):
    """
    Returns detailed level progression history including:
    - All level snapshots with course/instructor info
    - Student enrollment counts per level
    - Session completion tracking
    """
    history = svc.get_level_progression_history(group_id)
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/enrollments/analytics",
    response_model=ApiResponse[GroupEnrollmentHistoryResponseDTO],
    summary="Get full enrollment history with payment details",
)
def get_group_enrollment_analytics(
    group_id: int,
    status: str | None = Query(None, description="Filter by status (active, completed, dropped)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    _user: User = Depends(require_any),
    svc: GroupAnalyticsService = Depends(get_group_analytics_service),
):
    """
    Returns comprehensive enrollment history including:
    - Student contact information
    - Enrollment status and dates
    - Payment calculations (amount due, discount, payments made, balance)
    - Pagination support
    """
    history = svc.get_enrollment_history(group_id, status, skip, limit)
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/instructors/analytics",
    response_model=ApiResponse[GroupInstructorHistoryResponseDTO],
    summary="Get instructor assignment history",
)
def get_group_instructors_analytics(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupAnalyticsService = Depends(get_group_analytics_service),
):
    """
    Returns instructor assignment history including:
    - Unique instructors who have taught the group
    - Levels taught count per instructor
    - Assignment date ranges
    - Current instructor designation
    """
    history = svc.get_instructor_history(group_id)
    return ApiResponse(data=history)


# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS ENDPOINTS (for frontend compatibility)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/academics/groups/{group_id}/enrollment-history",
    response_model=ApiResponse[GroupEnrollmentHistoryResponseDTO],
    summary="Get enrollment history (alias for /enrollments/analytics)",
)
def get_group_enrollment_history_alias(
    group_id: int,
    status: str | None = Query(None, description="Filter by status (active, completed, dropped)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    _user: User = Depends(require_any),
    svc: GroupAnalyticsService = Depends(get_group_analytics_service),
):
    """Alias for /enrollments/analytics - returns enrollment history."""
    history = svc.get_enrollment_history(group_id, status, skip, limit)
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/instructor-history",
    response_model=ApiResponse[GroupInstructorHistoryResponseDTO],
    summary="Get instructor history (alias for /instructors/analytics)",
)
def get_group_instructor_history_alias(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupAnalyticsService = Depends(get_group_analytics_service),
):
    """Alias for /instructors/analytics - returns instructor assignment history."""
    history = svc.get_instructor_history(group_id)
    return ApiResponse(data=history)
