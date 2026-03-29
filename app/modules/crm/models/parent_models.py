"""
app/modules/crm/models/parent_models.py
──────────────────────────────────────────
SQLModel table definition for the Parent entity.
StudentParent junction lives in link_models.py to avoid circular refs.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.crm.models.link_models import StudentParent


class ParentBase(SQLModel):
    full_name: str
    phone_primary: Optional[str] = None  # unique enforced at DB level
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None


class Parent(ParentBase, table=True):
    __tablename__ = "parents"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    student_links: List["StudentParent"] = Relationship(back_populates="parent")


class ParentCreate(ParentBase):
    """DTO for creating a new parent via bulk/seed operations."""
    pass


class ParentRead(ParentBase):
    """Network-safe read representation."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
