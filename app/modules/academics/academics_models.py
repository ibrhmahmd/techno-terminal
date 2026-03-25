from datetime import datetime, time
from typing import Any, Optional

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Column, String
from app.shared.constants import GroupStatus

# --- Course Schemas ---

class CourseBase(SQLModel):
    name: str = Field(unique=True)
    category: Optional[str] = None  # schema CHECK: 'software','hardware','steam','other'
    price_per_level: float  # schema: price_per_level (not price_egp)
    sessions_per_level: int = 5
    description: Optional[str] = None
    is_active: bool = True

class Course(CourseBase, table=True):
    __tablename__ = "courses"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Group Models ---

class GroupBase(SQLModel):
    name: Optional[str] = None
    course_id: int = Field(foreign_key="courses.id")
    instructor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    level_number: int = 1
    max_capacity: Optional[int] = None
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None
    default_time_end: Optional[time] = None
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
