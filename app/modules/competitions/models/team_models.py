from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlmodel import SQLModel, Field

# Ensure related models are loaded so SQLAlchemy can resolve foreign keys
import app.modules.finance  # noqa: F401
import app.modules.crm  # noqa: F401
import app.modules.academics.models  # noqa: F401


# --- Team Models ---

class TeamBase(SQLModel):
    competition_id: int = Field(foreign_key="competitions.id")  # Direct FK to competition
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    # Category/subcategory stored as citext in DB (case-insensitive)
    category: str  # Required category name
    subcategory: Optional[str] = None  # Optional subcategory
    fee: Optional[Decimal] = None  # Academy-set fee for this team
    placement_rank: Optional[int] = None  # 1=1st place, 2=2nd, etc.
    placement_label: Optional[str] = None  # "Gold", "3rd Place", etc.
    notes: Optional[str] = None  # Additional notes

class Team(TeamBase, table=True):
    __tablename__ = "teams"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None  # Soft delete timestamp
    deleted_by: Optional[int] = Field(default=None, foreign_key="users.id")  # Who soft deleted

    # Use explicit SQLAlchemy column for citext type
    # Note: The actual citext type is set at the database level via migration


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
