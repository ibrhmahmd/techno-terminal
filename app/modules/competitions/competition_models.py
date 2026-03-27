from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field

# Ensure related models are loaded so SQLAlchemy can resolve foreign keys
import app.modules.finance.finance_models
import app.modules.crm
import app.modules.academics.models
import app.modules.auth
import app.modules.enrollments.enrollment_models


# --- Competition Schemas ---

class CompetitionBase(SQLModel):
    name: str
    edition: Optional[str] = None
    competition_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class Competition(CompetitionBase, table=True):
    __tablename__ = "competitions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None

class CompetitionCreate(CompetitionBase):
    pass

class CompetitionRead(CompetitionBase):
    id: int
    created_at: Optional[datetime] = None


# --- Competition Category Schemas ---

class CompetitionCategoryBase(SQLModel):
    competition_id: int = Field(foreign_key="competitions.id")
    category_name: str
    notes: Optional[str] = None

class CompetitionCategory(CompetitionCategoryBase, table=True):
    __tablename__ = "competition_categories"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

class CompetitionCategoryCreate(CompetitionCategoryBase):
    pass

class CompetitionCategoryRead(CompetitionCategoryBase):
    id: int


# --- Team Schemas ---

class TeamBase(SQLModel):
    category_id: int = Field(foreign_key="competition_categories.id")
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    enrollment_fee_per_student: Optional[float] = None

class Team(TeamBase, table=True):
    __tablename__ = "teams"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    team_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=SAColumn("metadata", JSONB),
    )

class TeamCreate(TeamBase):
    pass

class TeamRead(TeamBase):
    id: int
    created_at: Optional[datetime] = None


# --- Team Member Schemas ---

class TeamMemberBase(SQLModel):
    team_id: int = Field(foreign_key="teams.id")
    student_id: int = Field(foreign_key="students.id")
    fee_paid: bool = False
    payment_id: Optional[int] = Field(default=None, foreign_key="payments.id")

class TeamMember(TeamMemberBase, table=True):
    __tablename__ = "team_members"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberRead(TeamMemberBase):
    id: int
