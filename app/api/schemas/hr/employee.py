"""
app/api/schemas/hr/employee.py
──────────────────────────────
Public-facing Employee DTOs (safe fields only).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.modules.hr.constants import EmploymentType


class EmployeePublic(BaseModel):
    """
    Safe employee view for API consumers.
    """
    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    national_id: str
    job_title: Optional[str] = None
    employment_type: str
    is_active: bool
    hired_at: Optional[datetime] = None
    has_account: bool = Field(default=False, description="Whether employee has a linked user account")
    university: Optional[str] = None
    major: Optional[str] = None
    is_graduate: Optional[bool] = None
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = None
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Populated only when the row is soft-deleted and "
        "returned via include_deleted=true",
    )
    deleted_by: Optional[int] = Field(
        default=None,
        description="Local user ID of the admin who deleted the employee",
    )

    model_config = {"from_attributes": True}


class EmployeeListItem(BaseModel):
    """Slim employee for list views."""
    id: int
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: str
    is_active: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None

    model_config = {"from_attributes": True}


class EmployeeCreateInput(BaseModel):
    """
    Input for creating/updating an employee via API.
    Includes all fields needed for HR operations.
    """
    full_name: str
    phone: str
    email: Optional[str] = None
    national_id: str
    university: str
    major: str
    is_graduate: bool = False
    job_title: Optional[str] = None
    employment_type: str  # full_time, part_time, contract
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class EmployeeUpdateInput(BaseModel):
    """
    Partial-update input for an employee via API. All fields optional;
    only provided fields are applied.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?\d{10,}$")
    email: Optional[str] = Field(None, max_length=255)
    national_id: Optional[str] = Field(None, min_length=10)
    university: Optional[str] = Field(None, min_length=1, max_length=100)
    major: Optional[str] = Field(None, min_length=1, max_length=100)
    is_graduate: Optional[bool] = None
    job_title: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = None  # full_time, part_time, contract
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = None
    is_active: Optional[bool] = None

    model_config = {"from_attributes": True}


class StaffAccountPublic(BaseModel):
    """
    Public view of staff account with linked employee info.
    Returned by list_staff_accounts endpoint.
    """
    id: int
    username: str
    email: Optional[str] = None
    employee_id: int
    employee_name: str
    job_title: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
