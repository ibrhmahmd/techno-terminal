from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# --- Guardian Schemas ---

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

    # Relationship
    student_links: List["StudentGuardian"] = Relationship(
        back_populates="guardian"
    )

class GuardianCreate(GuardianBase):
    pass

class GuardianRead(GuardianBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Student Schemas ---

class StudentBase(SQLModel):
    full_name: str
    date_of_birth: Optional[datetime] = None  # schema: date_of_birth (DATE)
    gender: Optional[str] = None  # schema CHECK: 'male' / 'female' lowercase
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

    # Relationship
    guardian_links: List["StudentGuardian"] = Relationship(
        back_populates="student"
    )

class StudentCreate(StudentBase):
    pass

class StudentRead(StudentBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Junction Schemas ---

class StudentGuardian(SQLModel, table=True):
    __tablename__ = "student_guardians"
    __table_args__ = {"extend_existing": True}

    student_id: int = Field(foreign_key="students.id", primary_key=True)
    guardian_id: int = Field(foreign_key="guardians.id", primary_key=True)
    relationship: Optional[str] = None
    is_primary: bool = False  # schema: is_primary (not is_primary_contact)
    created_at: Optional[datetime] = None

    # Relationships
    student: "Student" = Relationship(
        back_populates="guardian_links"
    )
    guardian: "Guardian" = Relationship(
        back_populates="student_links"
    )
