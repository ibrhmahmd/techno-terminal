from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field

# Ensure related models are loaded so SQLAlchemy can resolve foreign keys
import app.modules.finance
import app.modules.crm
import app.modules.academics.models
import app.modules.auth
import app.modules.enrollments.models.enrollment_models  # noqa: F401


# --- Competition Models ---

class CompetitionBase(SQLModel):
    name: str
    edition: Optional[str] = None  # Deprecated: use edition_year
    edition_year: int  # New: the year of this competition edition
    competition_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    fee_per_student: float = Field(default=0.0)

class Competition(CompetitionBase, table=True):
    __tablename__ = "competitions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None  # Soft delete timestamp
    deleted_by: Optional[int] = Field(default=None, foreign_key="users.id")  # Who soft deleted
