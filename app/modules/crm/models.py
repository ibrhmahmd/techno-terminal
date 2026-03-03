from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class StudentGuardian(SQLModel, table=True):
    __tablename__ = "student_guardians"
    __table_args__ = {"extend_existing": True}

    student_id: int = Field(foreign_key="students.id", primary_key=True)
    guardian_id: int = Field(foreign_key="guardians.id", primary_key=True)
    relationship: Optional[str] = None
    is_primary: bool = False  # schema: is_primary (not is_primary_contact)
    created_at: Optional[datetime] = None

    # Link objects directly
    student: Optional["Student"] = Relationship(back_populates="guardian_links")
    guardian: Optional["Guardian"] = Relationship()


class Guardian(SQLModel, table=True):
    __tablename__ = "guardians"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    phone_primary: Optional[str] = None  # unique enforced at DB level
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationship back to students
    students: List["Student"] = Relationship(
        back_populates="guardians", link_model=StudentGuardian
    )


class Student(SQLModel, table=True):
    __tablename__ = "students"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    date_of_birth: Optional[datetime] = None  # schema: date_of_birth (DATE)
    gender: Optional[str] = None  # schema CHECK: 'male' / 'female' lowercase
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationship back to guardians
    guardians: List["Guardian"] = Relationship(
        back_populates="students", link_model=StudentGuardian
    )

    # For fetching the link rows directly
    guardian_links: List["StudentGuardian"] = Relationship(back_populates="student")
