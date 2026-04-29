"""
app/api/routers/academics/group_details_router.py
────────────────────────────────────────────────
Group Details API router.

Endpoints for detailed group management:
- DELETE level (with constraints)
- GET levels/detailed (with lookup tables)
- GET attendance (grid)
- GET finance/payments
- GET enrollments/all

Auth: GET=require_any, DELETE=require_admin
"""
from fastapi import APIRouter, Depends, Path, HTTPException, status, Query

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin
from app.modules.academics.services.group_details_service import GroupDetailsService
from app.modules.academics.schemas.group_details_schemas import (
    LevelDeleteResultDTO,
    GroupLevelsDetailedResponseDTO,
    GroupAttendanceResponseDTO,
    GroupPaymentsResponseDTO,
    GroupEnrollmentsResponseDTO,
)
from app.shared.exceptions import NotFoundError, ConflictError

router = APIRouter(tags=["Academics — Group Details"])


def get_group_details_service() -> GroupDetailsService:
    """Dependency provider for GroupDetailsService."""
    return GroupDetailsService()


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /academics/groups/{group_id}/levels/{level_number}
# ═══════════════════════════════════════════════════════════════════════════════

@router.delete(
    "/academics/groups/{group_id}/levels/{level_number}",
    response_model=ApiResponse[LevelDeleteResultDTO],
    summary="Delete a level (soft delete)",
    responses={
        404: {"description": "Level not found"},
        409: {"description": "Level has sessions or enrollments - cannot delete"},
    },
)
def delete_level(
    group_id: int = Path(..., ge=1, description="Group ID"),
    level_number: int = Path(..., ge=1, description="Level number"),
    _user=Depends(require_admin),
    svc: GroupDetailsService = Depends(get_group_details_service),
):
    """
    Soft delete a level if it has no sessions or enrollments.
    
    Returns the deleted level info including deletion timestamp.
    
    **Error cases:**
    - 404: Level not found
    - 409: Level has scheduled sessions
    - 409: Level has active enrollments
    """
    try:
        result = svc.delete_level(group_id, level_number)
        return ApiResponse(
            data=result,
            message=f"Level {level_number} deleted successfully.",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# GET /academics/groups/{group_id}/levels/detailed
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/academics/groups/{group_id}/levels/detailed",
    response_model=ApiResponse[GroupLevelsDetailedResponseDTO],
    summary="Get all levels (or specific level) with sessions and stats",
)
def get_levels_detailed(
    group_id: int = Path(..., ge=1, description="Group ID"),
    level_number: int | None = Query(None, ge=1, description="Specific level number (omit for all levels)"),
    _user=Depends(require_any),
    svc: GroupDetailsService = Depends(get_group_details_service),
):
    """
    Get detailed information about group levels.
    
    Query Param:
    - `level_number`: Optional. If provided, returns only that specific level.
    - If omitted, returns all levels for the group.
    
    Returns:
    - Lookup tables for courses and instructors (deduplicated)
    - Levels with their sessions (all or single based on query param)
    - Enrollment counts per level
    - Payment summaries per level
    
    Uses lookup table pattern to minimize data duplication.
    Response is cacheable (cache_ttl: 300 seconds).
    """
    result = svc.get_levels_detailed(group_id, level_number)
    return ApiResponse(
        data=result,
        message=f"Level{'s' if level_number is None else f' {level_number}'} loaded successfully.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GET /academics/groups/{group_id}/attendance
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/academics/groups/{group_id}/attendance",
    response_model=ApiResponse[GroupAttendanceResponseDTO],
    summary="Get attendance grid for a level",
)
def get_attendance(
    group_id: int = Path(..., ge=1, description="Group ID"),
    level_number: int = Query(..., ge=1, description="Level number"),
    _user=Depends(require_any),
    svc: GroupDetailsService = Depends(get_group_details_service),
):
    """
    Get attendance data for a specific group level.
    
    Returns:
    - Roster: Active enrollments with billing status
    - Sessions: All sessions for the level
    - Attendance map: O(1) lookup by student_id per session
    
    Query param:
    - `level_number` (required): The level to get attendance for
    """
    result = svc.get_attendance_grid(group_id, level_number)
    return ApiResponse(
        data=result,
        message="Attendance grid loaded successfully.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GET /finance/groups/{group_id}/payments
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/finance/groups/{group_id}/payments",
    response_model=ApiResponse[GroupPaymentsResponseDTO],
    summary="Get payments grouped by level",
)
def get_group_payments(
    group_id: int = Path(..., ge=1, description="Group ID"),
    _user=Depends(require_any),
    svc: GroupDetailsService = Depends(get_group_details_service),
):
    """
    Get payments grouped by level for the Payments tab.
    
    Returns:
    - Summary: Total expected, collected, due across all levels
    - Per-level breakdown with payment list
    """
    result = svc.get_group_payments(group_id)
    return ApiResponse(
        data=result,
        message="Group payments loaded successfully.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GET /academics/groups/{group_id}/enrollments/all
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/academics/groups/{group_id}/enrollments/all",
    response_model=ApiResponse[GroupEnrollmentsResponseDTO],
    summary="Get all enrollments grouped by level",
)
def get_group_enrollments(
    group_id: int = Path(..., ge=1, description="Group ID"),
    _user=Depends(require_any),
    svc: GroupDetailsService = Depends(get_group_details_service),
):
    """
    Get all enrollments grouped by level for the Students tab.
    
    Returns:
    - Students lookup table (student_id -> info)
    - Enrollments grouped by level
    - Per-level summary stats
    - Transfer options (available groups)
    """
    result = svc.get_group_enrollments(group_id)
    return ApiResponse(
        data=result,
        message="Group enrollments loaded successfully.",
    )
