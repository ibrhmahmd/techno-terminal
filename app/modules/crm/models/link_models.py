"""
app/modules/crm/models/link_models.py
──────────────────────────────────────
StudentParent junction table.
Isolated here to break the circular import that would arise if this were
placed in either parent_models.py or student_models.py.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.student_models import Student


class StudentParent(SQLModel, table=True):
    __tablename__ = "student_parents"
    __table_args__ = {"extend_existing": True}

    student_id: int = Field(foreign_key="students.id", primary_key=True)
    parent_id: int = Field(foreign_key="parents.id", primary_key=True)
    relationship: Optional[str] = None
    is_primary: bool = False  # schema: is_primary (not is_primary_contact)
    created_at: Optional[datetime] = None

    student: Student = Relationship(back_populates="parent_links")
    parent: Parent = Relationship(back_populates="student_links")
