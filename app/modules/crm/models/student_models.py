"""
app/modules/crm/models/student_models.py
─────────────────────────────────────────
SQLModel table definition for the Student entity.
StudentParent junction lives in link_models.py to avoid circular refs.
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.crm.models.link_models import StudentParent


class StudentStatus(str, Enum):
    """Enum for student enrollment status."""
    ACTIVE = "active"
    WAITING = "waiting"
    INACTIVE = "inactive"


class StudentBase(SQLModel):
    full_name: str
    date_of_birth: Optional[datetime] = None  # column type: DATE
    gender: Optional[str] = None              # CHECK: 'male' | 'female'
    phone: Optional[str] = None
    notes: Optional[str] = None
    # NEW FIELD: Use String type to match database enum
    # Default to WAITING - student becomes ACTIVE upon first enrollment
    status: StudentStatus = Field(
        default=StudentStatus.WAITING,
        sa_column=Column(String, default="waiting")
    )


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
    # NEW: Waiting list metadata fields
    waiting_since: Optional[datetime] = None
    waiting_priority: Optional[int] = None
    waiting_notes: Optional[str] = None
    
    # NEW: Soft delete fields
    deleted_at: Optional[datetime] = Field(default=None, description="Soft delete timestamp")
    deleted_by: Optional[int] = Field(default=None, foreign_key="users.id")
    
    parent_links: List["StudentParent"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class StudentCreate(StudentBase):
    """DTO for creating a student via bulk/seed operations."""
    pass



class StudentRead(StudentBase):
    """Network-safe read representation."""
    id: int
    status: str
    waiting_since: Optional[datetime] = None
    waiting_priority: Optional[int] = None
    waiting_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Soft delete fields
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
