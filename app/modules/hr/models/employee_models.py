"""Employee Models

SQLModel entities for employee management.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field

from app.modules.hr.constants import EmploymentType


class EmployeeBase(SQLModel):
    """Base employee fields shared across all models."""
    full_name: str
    phone: str
    email: Optional[str] = None
    national_id: str
    university: str
    major: str
    is_graduate: bool = False
    job_title: Optional[str] = None
    employment_type: EmploymentType = Field(sa_column=Column(String))
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = None
    is_active: bool = True


class Employee(EmployeeBase, table=True):
    """Employee database model."""
    __tablename__ = "employees"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", unique=True)
    employee_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSONB),
    )
