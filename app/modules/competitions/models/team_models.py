from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field

# Ensure related models are loaded so SQLAlchemy can resolve foreign keys
import app.modules.finance.finance_models
import app.modules.crm
import app.modules.academics.models
import app.modules.auth
import app.modules.enrollments.models.enrollment_models
from app.modules.competitions.models.competition_models import CompetitionCategory


# --- Team Models ---

class TeamBase(SQLModel):
    category_id: int = Field(foreign_key="competition_categories.id")
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")

class Team(TeamBase, table=True):
    __tablename__ = "teams"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    team_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=SAColumn("metadata", JSONB),
    )


# --- Team Member Models ---

class TeamMemberBase(SQLModel):
    team_id: int = Field(foreign_key="teams.id")
    student_id: int = Field(foreign_key="students.id")
    member_share: float = Field(default=0.0)
    fee_paid: bool = False
    payment_id: Optional[int] = Field(default=None, foreign_key="payments.id")

class TeamMember(TeamMemberBase, table=True):
    __tablename__ = "team_members"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
