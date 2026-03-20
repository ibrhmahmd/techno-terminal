from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column, String
from app.shared.constants import EnrollmentStatus

# --- Enrollment Schemas ---

class EnrollmentBase(SQLModel):
    student_id: int = Field(foreign_key="students.id")
    group_id: int = Field(foreign_key="groups.id")
    level_number: int  # Snapshot from group at enrollment time
    amount_due: Optional[float] = None  # Custom per-student amount
    discount_applied: float = 0.0
    status: EnrollmentStatus = Field(default="active", sa_column=Column(String))
    transferred_from: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    notes: Optional[str] = None

class Enrollment(EnrollmentBase, table=True):
    __tablename__ = "enrollments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    enrolled_at: Optional[datetime] = None
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentRead(EnrollmentBase):
    id: int
    enrolled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
