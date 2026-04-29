"""Employee Models

SQLModel entities for employee management.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import field_validator
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field

from app.shared.constants import EmploymentType


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


class EmployeeCreate(EmployeeBase):
    """DTO for creating a new employee."""
    
    @field_validator("phone", "national_id", "university", "major", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_none(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip()

    @field_validator("national_id")
    @classmethod
    def national_id_len(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("National ID must be at least 10 characters.")
        return v


class EmployeeRead(EmployeeBase):
    """DTO for reading employee data."""
    id: int
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
