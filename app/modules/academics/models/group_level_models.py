"""
app/modules/academics/models/group_level_models.py
───────────────────────────────────────────────────
SQLModel classes for Group Levels (OTS Levels), Course History,
and Competition Participation tracking.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field, Column, String
from app.modules.academics.constants import DEFAULT_SESSIONS_PER_LEVEL
from app.shared.datetime_utils import utc_now


class GroupLevel(SQLModel, table=True):
    """Immutable per-level configuration snapshot for a group."""
    __tablename__ = "group_levels"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    level_number: int = Field(index=True)
    course_id: int = Field(foreign_key="courses.id")
    instructor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    sessions_planned: int = Field(default=DEFAULT_SESSIONS_PER_LEVEL)
    price_override: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    status: str = Field(default="active", sa_column=Column(String, index=True))
    effective_from: datetime = Field(default_factory=utc_now)
    effective_to: Optional[datetime] = None
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = Field(default_factory=utc_now)


class GroupCourseHistory(SQLModel, table=True):
    """Audit trail for course assignments to groups."""
    __tablename__ = "group_course_history"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    course_id: int = Field(foreign_key="courses.id")
    assigned_at: datetime = Field(default_factory=utc_now)
    removed_at: Optional[datetime] = None
    assigned_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=utc_now)


