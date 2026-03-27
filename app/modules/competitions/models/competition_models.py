from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field

# Ensure related models are loaded so SQLAlchemy can resolve foreign keys
import app.modules.finance.finance_models
import app.modules.crm
import app.modules.academics.models
import app.modules.auth
import app.modules.enrollments.enrollment_models


# --- Competition Models ---

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


# --- Competition Category Models ---

class CompetitionCategoryBase(SQLModel):
    competition_id: int = Field(foreign_key="competitions.id")
    category_name: str
    notes: Optional[str] = None

class CompetitionCategory(CompetitionCategoryBase, table=True):
    __tablename__ = "competition_categories"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
