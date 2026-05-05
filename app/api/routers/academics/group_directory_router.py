"""
app/api/routers/academics/group_directory_router.py
────────────────────────────────────────────────────
Group Directory router.

Handles all group listing, searching, filtering, and grouped-display operations.
These are read-only operations served by GroupDirectoryService.

Auth: all endpoints require at least require_any (any authenticated user).
"""
from fastapi import APIRouter, Depends, Query, Path

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.group import (
    GroupListItem,
    EnrichedGroupPublic,
)
from app.api.schemas.academics.grouped import GroupedGroupsResponse, GroupedItem
from app.api.dependencies import require_any, get_group_directory_service
from app.modules.auth import User
from app.modules.academics.group.directory.service import GroupDirectoryService

router = APIRouter(tags=["Academics — Group Directory"])


# ── List all active groups ────────────────────────────────────────────────────

@router.get(
    "/academics/groups",
    response_model=PaginatedResponse[GroupListItem],
    summary="List all active groups",
)
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    results = svc.get_all_active_groups()
    page = results[skip : skip + limit]
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in page],
        total=len(results),
        skip=skip,
        limit=limit,
    )


# ── Enriched groups list (with instructor/course names) ──────────────────────

@router.get(
    "/academics/groups/enriched",
    response_model=ApiResponse[list[EnrichedGroupPublic]],
    summary="Get all active groups with instructor and course names",
)
def list_enriched_groups(
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    groups = svc.get_all_active_groups_enriched()
    if not groups:
        return ApiResponse(data=[])
    return ApiResponse(
        data=[EnrichedGroupPublic.model_validate(g.model_dump(mode="json")) for g in groups]
    )


# ── Archived groups ───────────────────────────────────────────────────────────

@router.get(
    "/academics/groups/archived",
    response_model=PaginatedResponse[GroupListItem],
    summary="Get archived groups (paginated)",
)
def list_archived_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    results = svc.get_all_archived_groups()
    page = results[skip : skip + limit]
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in page],
        total=len(results),
        skip=skip,
        limit=limit,
    )


# ── Search groups ─────────────────────────────────────────────────────────────
# NOTE: Must be registered before /{group_id} to avoid routing conflict.

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
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    """Search groups by name using partial matching."""
    results, total = svc.search_groups(query, status, skip, limit)
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in results],
        total=total,
        skip=skip,
        limit=limit,
    )


# ── Groups grouped by field ───────────────────────────────────────────────────

@router.get(
    "/academics/groups/grouped",
    response_model=ApiResponse[GroupedGroupsResponse],
    summary="Get groups grouped by a specific field (day, course, instructor, status)",
)
def list_groups_grouped(
    group_by: str = Query(..., description="Field to group by: day, course, instructor, status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    search: str | None = Query(None, description="Optional search term"),
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    result = svc.get_groups_grouped(
        group_by=group_by,
        skip=skip,
        limit=limit,
        search=search,
    )
    return ApiResponse(
        data=GroupedGroupsResponse(
            groups=[
                GroupedItem(
                    key=item.key,
                    label=item.label,
                    count=item.count,
                    groups=[EnrichedGroupPublic.model_validate(g).model_dump() for g in item.groups],
                )
                for item in result.groups
            ],
            total=result.total,
            group_by=result.group_by,
        )
    )


# ── Groups by course ──────────────────────────────────────────────────────────

@router.get(
    "/academics/groups/by-course/{course_id}",
    response_model=PaginatedResponse[EnrichedGroupPublic],
    summary="Get all groups for a specific course",
)
def list_groups_by_course(
    course_id: int = Path(..., gt=0, description="Course ID"),
    include_inactive: bool = Query(False, description="Include inactive groups"),
    level_number: int | None = Query(None, gt=0, description="Filter by level number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
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


# ── Groups by type ────────────────────────────────────────────────────────────

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
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    """Get groups filtered by type."""
    results, total = svc.get_groups_by_type(group_type, status, skip, limit)
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in results],
        total=total,
        skip=skip,
        limit=limit,
    )


# ── Enriched group by ID ──────────────────────────────────────────────────────

@router.get(
    "/academics/groups/{group_id}/enriched",
    response_model=ApiResponse[EnrichedGroupPublic],
    summary="Get enriched group by ID (with course and instructor names)",
)
def get_enriched_group(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    from fastapi import HTTPException
    group = svc.get_enriched_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return ApiResponse(data=EnrichedGroupPublic.model_validate(group.model_dump(mode="json")))
