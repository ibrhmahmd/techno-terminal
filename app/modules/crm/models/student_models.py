"""
app/modules/crm/models/student_models.py
─────────────────────────────────────────
SQLModel table definition for the Student entity.
StudentGuardian junction lives in link_models.py to avoid circular refs.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.crm.models.link_models import StudentGuardian


class StudentBase(SQLModel):
    full_name: str
    date_of_birth: Optional[datetime] = None  # column type: DATE
    gender: Optional[str] = None              # CHECK: 'male' | 'female'
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class Student(StudentBase, table=True):
    __tablename__ = "students"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    profile_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSONB),
    )
    guardian_links: List["StudentGuardian"] = Relationship(back_populates="student")


class StudentCreate(StudentBase):
    """DTO for creating a student via bulk/seed operations."""
    pass


class StudentRead(StudentBase):
    """Network-safe read representation."""
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
