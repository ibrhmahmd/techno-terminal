"""
app/modules/enrollments/api/schemas/progress.py
───────────────────────────────────────────────
HTTP schemas for POST /academics/groups/{id}/progress-level (served by enrollments).
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ProgressGroupLevelRequest(BaseModel):
    """
    Request body for POST /academics/groups/{id}/progress-level.
    Progress group to next level.
    """
    price_override: Optional[Decimal] = None  # None/0 uses course default price
    target_level: Optional[int] = None  # If None, defaults to current + 1
    auto_migrate_enrollments: bool = True  # If False, creates empty level
    complete_current_level: bool = True  # If False, keeps current level active
    instructor_id: Optional[int] = None  # Override group's default instructor
    session_start_date: Optional[date] = None  # Override default session start date (YYYY-MM-DD)
    course_id: Optional[int] = None  # Override group's course
    group_name: Optional[str] = None  # Override group name


class ProgressGroupLevelResult(BaseModel):
    """Response for POST /academics/groups/{id}/progress-level."""
    old_level_number: int
    new_level_number: int
    enrollments_migrated: int
    sessions_created: int
    message: str
