"""
app/modules/academics/models/group_models.py
────────────────────────────────────────────
SQLModel classes for the Group entity.
"""
from datetime import datetime, time
from typing import Any, Optional

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Column, String
from app.modules.academics.constants import GroupStatus

class GroupBase(SQLModel):
    name: Optional[str] = None
    course_id: int = Field(foreign_key="courses.id")
    instructor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    level_number: int = 1
    max_capacity: Optional[int] = None
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None
    default_time_end: Optional[time] = None
    notes: Optional[str] = None
    status: GroupStatus = Field(default="active", sa_column=Column(String))

class Group(GroupBase, table=True):
    __tablename__ = "groups"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    group_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=SAColumn("metadata", JSONB),
    )

    @property
    def group_name(self) -> Optional[str]:
        """Alias for name field for DTO compatibility."""
        return self.name
