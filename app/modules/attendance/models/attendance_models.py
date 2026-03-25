from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, String
from sqlalchemy import UniqueConstraint
from app.shared.constants import AttendanceStatus


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "session_id", name="uq_attendance_student_session"),
        {"extend_existing": True}
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    session_id: int = Field(foreign_key="sessions.id")
    enrollment_id: int = Field(foreign_key="enrollments.id")
    status: AttendanceStatus = Field(sa_column=Column(String))  # CHECK: present / absent / late / excused
    marked_by: Optional[int] = Field(default=None, foreign_key="users.id")
    marked_at: Optional[datetime] = None
