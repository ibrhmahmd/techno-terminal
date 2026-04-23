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
from fastapi import APIRouter, Depends, Path, HTTPException, status

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin
from app.modules.academics.services.group_details_service import GroupDetailsService
from app.modules.academics.schemas.group_details_schemas import (
    LevelDeleteResultDTO,
    GroupLevelsDetailedResponseDTO,
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
    summary="Get all levels with sessions and stats",
)
def get_levels_detailed(
    group_id: int = Path(..., ge=1, description="Group ID"),
    _user=Depends(require_any),
    svc: GroupDetailsService = Depends(get_group_details_service),
):
    """
    Get detailed information about all group levels.
    
    Returns:
    - Lookup tables for courses and instructors (deduplicated)
    - All levels with their sessions
    - Enrollment counts per level
    - Payment summaries per level
    
    Uses lookup table pattern to minimize data duplication.
    Response is cacheable (cache_ttl: 300 seconds).
    """
    result = svc.get_levels_detailed(group_id)
    return ApiResponse(
        data=result,
        message="Group levels loaded successfully.",
    )
