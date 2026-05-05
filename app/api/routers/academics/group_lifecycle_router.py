"""
app/api/routers/academics/group_lifecycle_router.py
───────────────────────────────────────────────────
Router for group level lifecycle and analytics endpoints.

Covers:
- Level detail retrieval
- Level completion and cancellation
- Enrollment analytics
- Instructor assignment analytics

Auth: GET = require_any, mutations = require_admin.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse
from app.api.dependencies import (
    require_any,
    require_admin,
    get_group_level_service,
    get_group_analytics_service,
)
from app.modules.auth import User
from app.modules.academics.group.level.service import GroupLevelService
from app.modules.academics.group.analytics.service import GroupAnalyticsService
from app.modules.academics.group.analytics.schemas import (
    GroupEnrollmentHistoryResponseDTO,
    GroupInstructorHistoryResponseDTO,
)
from app.api.schemas.academics.group_lifecycle import CancelLevelInput, CancelLevelResult
from app.api.schemas.academics.group_level import (
    GroupLevelPublic,
    GroupLevelCompletionResponse,
    GroupLevelSummary,
)

router = APIRouter(tags=["Academics — Group Lifecycle"])


# ── GET /academics/groups/{group_id}/levels/{level_number} ───────────────────

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
    """Returns detailed level information including course and instructor names."""
    level = svc.get_level_by_number(group_id, level_number)
    return ApiResponse(data=GroupLevelPublic.model_validate(level))


# ── POST /academics/groups/{group_id}/levels/{level_number}/complete ──────────

@router.post(
    "/academics/groups/{group_id}/levels/{level_number}/complete",
    response_model=ApiResponse[GroupLevelCompletionResponse],
    summary="Complete a level and progress to next",
)
def complete_group_level(
    group_id: int,
    level_number: int,
    _user: User = Depends(require_admin),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Mark a level as completed and create the next level snapshot.
    Requires admin privileges.
    """
    try:
        completed, new_level = svc.complete_current_level(group_id)
        return ApiResponse(
            data=GroupLevelCompletionResponse(
                completed_level=GroupLevelSummary(
                    id=completed.id,
                    group_id=completed.group_id,
                    level_number=completed.level_number,
                    status=completed.status,
                ),
                new_level=GroupLevelSummary(
                    id=new_level.id,
                    group_id=new_level.group_id,
                    level_number=new_level.level_number,
                    status=new_level.status,
                ),
                message=f"Group progressed from level {completed.level_number} to level {new_level.level_number}",
            ),
            message=f"Group progressed from level {completed.level_number} to level {new_level.level_number}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── POST /academics/groups/{group_id}/levels/{level_number}/cancel ────────────

@router.post(
    "/academics/groups/{group_id}/levels/{level_number}/cancel",
    response_model=ApiResponse[CancelLevelResult],
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
        from app.shared.datetime_utils import utc_now
        return ApiResponse(
            data=CancelLevelResult(
                level_id=cancelled_level.id,
                level_number=cancelled_level.level_number,
                status=cancelled_level.status,
                cancelled_at=cancelled_level.updated_at or utc_now(),
                reason=body.reason,
            ),
            message=f"Level {level_number} cancelled successfully.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── GET /academics/groups/{group_id}/enrollments/analytics ───────────────────

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
    Returns comprehensive enrollment history including student contact info,
    enrollment status, and payment calculations (amount due, discount, balance).
    """
    history = svc.get_enrollment_history(group_id, status, skip, limit)
    return ApiResponse(data=history)


# ── GET /academics/groups/{group_id}/instructors/analytics ───────────────────

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
    Returns instructor assignment history including unique instructors,
    levels taught count, assignment date ranges, and current instructor.
    """
    history = svc.get_instructor_history(group_id)
    return ApiResponse(data=history)


# ── Alias endpoints (frontend compatibility) ─────────────────────────────────

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
    """Alias for /enrollments/analytics — returns enrollment history."""
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
    """Alias for /instructors/analytics — returns instructor assignment history."""
    history = svc.get_instructor_history(group_id)
    return ApiResponse(data=history)
