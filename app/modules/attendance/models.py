from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    session_id: int = Field(foreign_key="sessions.id")
    enrollment_id: int = Field(foreign_key="enrollments.id")
    status: str  # CHECK: present / absent / late / excused
    marked_by: Optional[int] = Field(default=None, foreign_key="users.id")
    marked_at: Optional[datetime] = None
