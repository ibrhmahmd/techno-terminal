"""
app/api/routers/academics/group_directory_router.py
────────────────────────────────────────────────────
Group Directory router.

Handles all group listing, searching, filtering, and grouped-display operations.
These are read-only operations served by GroupDirectoryService.

Auth: all endpoints require at least require_any (any authenticated user).
"""
from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.group import (
    EnrichedGroupPublic,
)
from app.api.schemas.academics.grouped import GroupedGroupsResponse, GroupedItem
from app.api.dependencies import require_any, get_group_directory_service
from app.modules.auth import User
from app.modules.academics.group.directory.service import GroupDirectoryService
from app.modules.academics.group.directory.schemas import GroupFilterDTO, GroupFilterResultDTO
from app.modules.academics.constants import DAY_ABBREV_MAP

router = APIRouter(tags=["Academics — Group Directory"])




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




# ── Filter groups (multi-criteria) ───────────────────────────────────────────
# NOTE: Must be registered before /{group_id} to avoid routing conflict.

def _normalize_day_names(days: Optional[List[str]]) -> Optional[List[str]]:
    """Convert day abbreviations to canonical full names (e.g. 'fri' → 'Friday')."""
    if not days:
        return days
    return [DAY_ABBREV_MAP.get(d.lower(), d) for d in days]


@router.get(
    "/academics/groups/filter",
    response_model=ApiResponse[GroupFilterResultDTO],
    summary="Filter groups by multiple criteria",
    description=(
        "Multi-criteria filter for groups. Supports free-text search (q), "
        "course, instructor, day, status, price, date/time range, session number, "
        "and paginated results sorted by name, day, or status."
    ),
)
def filter_groups(
    q: Optional[str] = Query(None, description="Free-text search across name, course, instructor, notes, schedule time, enrolled students"),
    name: Optional[str] = Query(None, description="Group name substring match"),
    course_ids: Optional[List[int]] = Query(None, description="Filter by course ID(s)"),
    course_name: Optional[str] = Query(None, description="Course name substring match"),
    day: Optional[List[str]] = Query(None, description="Day(s) of week — full names or abbreviations (fri, sat, …)"),
    instructor_id: Optional[int] = Query(None, description="Current instructor ID"),
    instructor_name: Optional[str] = Query(None, description="Partial instructor name match"),
    level_number: Optional[int] = Query(None, ge=1, description="Filter by level number (e.g. 1, 2, 3)"),
    status: Optional[List[str]] = Query(None, description="Group status(es): active, inactive, archived"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum course price per level"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum course price per level"),
    start_date_from: Optional[str] = Query(None, description="Sessions on or after this date (YYYY-MM-DD)"),
    start_date_to: Optional[str] = Query(None, description="Sessions on or before this date (YYYY-MM-DD)"),
    time_from: Optional[str] = Query(None, description="Default start time on or after (HH:MM)"),
    time_to: Optional[str] = Query(None, description="Default start time on or before (HH:MM)"),
    current_session_number: Optional[int] = Query(None, ge=1, description="Groups currently at this session number"),
    session_number_from: Optional[int] = Query(None, ge=1, description="Session number range start"),
    session_number_to: Optional[int] = Query(None, ge=1, description="Session number range end"),
    sort_by: Optional[str] = Query("name", description="Sort field: name, day, status"),
    sort_order: Optional[str] = Query("asc", description="Sort direction: asc, desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    """Filter groups by multiple criteria with pagination."""
    from datetime import date as _date, time as _time
    from fastapi import HTTPException

    # Parse date/time strings
    parsed_start_date_from = None
    parsed_start_date_to = None
    parsed_time_from = None
    parsed_time_to = None
    try:
        if start_date_from:
            parsed_start_date_from = _date.fromisoformat(start_date_from)
        if start_date_to:
            parsed_start_date_to = _date.fromisoformat(start_date_to)
        if time_from:
            h, m = time_from.split(":")
            parsed_time_from = _time(int(h), int(m))
        if time_to:
            h, m = time_to.split(":")
            parsed_time_to = _time(int(h), int(m))
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid date/time format: {exc}")

    # Validate sort_by
    valid_sort_by = {"name", "day", "status"}
    if sort_by not in valid_sort_by:
        sort_by = "name"
    valid_sort_order = {"asc", "desc"}
    if sort_order not in valid_sort_order:
        sort_order = "asc"

    filters = GroupFilterDTO(
        q=q,
        name=name,
        course_ids=course_ids,
        course_name=course_name,
        day=_normalize_day_names(day),
        instructor_id=instructor_id,
        instructor_name=instructor_name,
        level_number=level_number,
        status=status,
        price_min=price_min,
        price_max=price_max,
        start_date_from=parsed_start_date_from,
        start_date_to=parsed_start_date_to,
        time_from=parsed_time_from,
        time_to=parsed_time_to,
        current_session_number=current_session_number,
        session_number_from=session_number_from,
        session_number_to=session_number_to,
        sort_by=sort_by,  # type: ignore[arg-type]
        sort_order=sort_order,  # type: ignore[arg-type]
        skip=skip,
        limit=limit,
    )
    result = svc.filter_groups(filters)
    return ApiResponse(data=result)


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
