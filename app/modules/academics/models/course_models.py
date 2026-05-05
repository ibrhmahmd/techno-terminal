"""
app/modules/academics/models/course_models.py
─────────────────────────────────────────────
SQLModel classes for the Course entity.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class CourseBase(SQLModel):
    name: str = Field(unique=True)
    category: Optional[str] = None  # schema CHECK: 'software','hardware','steam','other'
    price_per_level: float  # schema: price_per_level (not price_egp)
    sessions_per_level: int = 4
    description: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class Course(CourseBase, table=True):
    __tablename__ = "courses"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
