"""
app/modules/hr/api/schemas.py
──────────────────────────────
HR HTTP request/response schemas (moved from app/api/schemas/hr/).
"""
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

from app.modules.hr.constants import EmploymentType
from app.shared.constants import MIN_PASSWORD_LENGTH


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
    hired_at: Optional[date] = None
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
    # Same constraints as CreateEmployeeDTO, so bad input is a 422 at the request boundary.
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\+?\d{10,}$")
    email: Optional[EmailStr] = Field(None, max_length=255)
    national_id: str = Field(..., min_length=10)
    university: str = Field(..., min_length=1, max_length=100)
    major: str = Field(..., min_length=1, max_length=100)
    is_graduate: bool = False
    job_title: Optional[str] = Field(None, max_length=100)
    employment_type: EmploymentType
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = None
    is_active: bool = True

    model_config = {"from_attributes": True, "str_strip_whitespace": True}


class EmployeeUpdateInput(BaseModel):
    """
    Partial-update input for an employee via API. All fields optional;
    only provided fields are applied.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?\d{10,}$")
    email: Optional[EmailStr] = Field(None, max_length=255)
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


class StaffAccountCreateInput(BaseModel):
    """Input for creating a staff account with linked employee."""
    employee: EmployeeCreateInput
    username: str
    role: str
    password: str


class StaffAccountUpdateInput(BaseModel):
    """Input for updating a staff account."""
    is_active: bool
    role: str


class CreateEmployeeAccountRequest(BaseModel):
    """Request body for creating an employee account."""
    email: EmailStr = Field(..., description="Account email address")
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        description=f"Account password (min {MIN_PASSWORD_LENGTH} characters)",
    )
    role: Literal["admin", "system_admin"] = Field(..., description="User role")


class EmployeeAccountResponse(BaseModel):
    """Response for created employee account."""
    employee_id: int = Field(..., description="Employee ID")
    user_id: int = Field(..., description="Created user ID")
    email: str = Field(..., description="Account email")
    role: str = Field(..., description="Assigned role")
    created_at: datetime = Field(..., description="Account creation timestamp")