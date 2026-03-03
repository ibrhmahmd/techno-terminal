from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field

# Ensure related models are loaded so SQLAlchemy can resolve foreign keys
import app.modules.finance.models
import app.modules.crm.models
import app.modules.academics.models
import app.modules.auth.models

class Competition(SQLModel, table=True):
    __tablename__ = "competitions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    edition: Optional[str] = None
    competition_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class CompetitionCategory(SQLModel, table=True):
    __tablename__ = "competition_categories"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    competition_id: int = Field(foreign_key="competitions.id")
    category_name: str
    notes: Optional[str] = None


class Team(SQLModel, table=True):
    __tablename__ = "teams"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="competition_categories.id")
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    enrollment_fee_per_student: Optional[float] = None
    created_at: Optional[datetime] = None


class TeamMember(SQLModel, table=True):
    __tablename__ = "team_members"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.id")
    student_id: int = Field(foreign_key="students.id")
    fee_paid: bool = False
    payment_id: Optional[int] = Field(default=None, foreign_key="payments.id")
