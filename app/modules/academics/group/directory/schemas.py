"""
app/modules/academics/group/directory/schemas.py
────────────────────────────────────────────────
Internal DTOs for Grouped Groups and Group Filtering.
"""
from datetime import date, time
from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator

from app.modules.academics.group.core.schemas import EnrichedGroupDTO


class GroupedItemDTO(BaseModel):
    """Internal DTO for a grouped item."""
    key: str
    label: str
    count: int
    groups: list[EnrichedGroupDTO]


class GroupedGroupsResult(BaseModel):
    """Result of getting grouped groups."""
    groups: list[GroupedItemDTO]
    total: int
    group_by: str


# ── Filter Input ──────────────────────────────────────────────────────────────

class GroupFilterDTO(BaseModel):
    """Input filter parameters for GET /academics/groups/filter.

    Cross-param logic: AND between different parameters, OR within a single
    parameter's multiple values (e.g., status=['active','inactive']).
    """
    # Free-text search across name, course name, instructor name, notes, time, enrolled students
    q: Optional[str] = None
    # Exact field filters (AND with other params, tighter than q)
    name: Optional[str] = None
    course_ids: Optional[List[int]] = None
    course_name: Optional[str] = None
    # Day filter — accepts full names or abbreviations; normalized before use
    day: Optional[List[str]] = None
    # Instructor filters
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    # Level (numeric rank on group, e.g. 1, 2, 3 — not the DB level_id)
    level_number: Optional[int] = None
    # Status
    status: Optional[List[str]] = None
    # Price range (from courses.price_per_level)
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    # Session date range (from sessions.session_date)
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    # Default schedule time range (from groups.default_time_start)
    time_from: Optional[time] = None
    time_to: Optional[time] = None
    # Session number filtering (from sessions.session_number)
    current_session_number: Optional[int] = None
    session_number_from: Optional[int] = None
    session_number_to: Optional[int] = None
    # Instructor presence
    has_instructor: Optional[bool] = None
    # Capacity filtering
    max_capacity_min: Optional[int] = None
    max_capacity_max: Optional[int] = None
    # Status handling toggle
    include_inactive: bool = False
    # Sorting
    sort_by: Optional[Literal["name", "day", "status"]] = "name"
    sort_order: Optional[Literal["asc", "desc"]] = "asc"
    # Pagination
    skip: int = 0
    limit: int = 50

    @field_validator("limit")
    @classmethod
    def cap_limit(cls, v: int) -> int:
        return min(v, 200)

    @field_validator("q", "name", "course_name", "instructor_name")
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v


# ── Filter Output ─────────────────────────────────────────────────────────────

class GroupFilterResultDTO(BaseModel):
    """Paginated output for the groups filter endpoint."""
    groups: list[EnrichedGroupDTO]
    total: int
    skip: int
    limit: int
