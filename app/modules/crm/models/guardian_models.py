"""
app/modules/crm/models/guardian_models.py
──────────────────────────────────────────
SQLModel table definition for the Guardian entity.
StudentGuardian junction lives in link_models.py to avoid circular refs.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.crm.models.link_models import StudentGuardian


class GuardianBase(SQLModel):
    full_name: str
    phone_primary: Optional[str] = None  # unique enforced at DB level
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None


class Guardian(GuardianBase, table=True):
    __tablename__ = "guardians"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    student_links: List["StudentGuardian"] = Relationship(back_populates="guardian")


class GuardianCreate(GuardianBase):
    """DTO for creating a new guardian via bulk/seed operations."""
    pass


class GuardianRead(GuardianBase):
    """Network-safe read representation."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
