from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field

# --- Employee Schemas ---

class EmployeeBase(SQLModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = None
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = 25.00
    is_active: bool = True

class Employee(EmployeeBase, table=True):
    __tablename__ = "employees"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    employee_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSONB),
    )

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeRead(EmployeeBase):
    id: int
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
