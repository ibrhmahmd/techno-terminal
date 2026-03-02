from datetime import time
from typing import Optional
from sqlmodel import SQLModel, Field


class CourseSession(SQLModel, table=True):
    """Maps to the 'sessions' table. Named CourseSession to avoid clashing with SQLModel's Session."""

    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id")
    level_number: int
    session_number: int
    session_date: Optional[str] = (
        None  # Stored as DATE; we handle as string for simplicity
    )
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    actual_instructor_id: Optional[int] = Field(
        default=None, foreign_key="employees.id"
    )
    is_substitute: bool = False
    is_extra_session: bool = False
    notes: Optional[str] = None
    created_at: Optional[str] = None
