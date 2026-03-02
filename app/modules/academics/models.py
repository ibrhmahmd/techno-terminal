from datetime import datetime, time
from typing import Optional
from sqlmodel import SQLModel, Field


class Course(SQLModel, table=True):
    __tablename__ = "courses"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    category: Optional[str] = (
        None  # schema CHECK: 'software','hardware','steam','other'
    )
    price_per_level: float  # schema: price_per_level (not price_egp)
    sessions_per_level: int = 5
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Group(SQLModel, table=True):
    __tablename__ = "groups"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    course_id: int = Field(foreign_key="courses.id")
    instructor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    level_number: int = 1
    max_capacity: Optional[int] = None
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None  # schema: default_time_start
    default_time_end: Optional[time] = None  # schema: default_time_end
    status: str = "active"
    started_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
