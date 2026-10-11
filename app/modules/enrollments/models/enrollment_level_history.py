"""Enrollment level history model.

Moved from ``app.modules.academics.models.group_level_models`` (ticket #19):
same ``__tablename__`` and columns, no schema change.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column, String
from app.shared.datetime_utils import utc_now


class EnrollmentLevelHistory(SQLModel, table=True):
    """Track student enrollment transitions through group levels."""
    __tablename__ = "enrollment_level_history"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    enrollment_id: int = Field(foreign_key="enrollments.id", index=True)
    group_level_id: int = Field(foreign_key="group_levels.id", index=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    level_entered_at: datetime = Field(default_factory=utc_now)
    level_completed_at: Optional[datetime] = None
    status: str = Field(default="active", sa_column=Column(String))
    created_at: Optional[datetime] = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = Field(default_factory=utc_now)
