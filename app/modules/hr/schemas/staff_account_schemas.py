"""Staff Account Schemas

Pydantic DTOs for employee-user account linking operations.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.constants import UserRole


class StaffAccountDTO(BaseModel):
    """Staff account with linked employee info - replaces list[dict]."""
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    employee_id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    phone: str


class CreateStaffAccountResultDTO(BaseModel):
    """Result of creating staff account with Supabase - replaces dict."""
    model_config = ConfigDict(frozen=True)

    user_id: int
    employee_id: int
    username: str
    supabase_uid: str


class CreateEmployeeAccountDTO(BaseModel):
    """DTO for creating account for existing employee."""
    model_config = ConfigDict(str_strip_whitespace=True)

    employee_id: int
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.ADMIN


class EmployeeAccountResultDTO(BaseModel):
    """Result of creating employee account."""
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    user_id: int
    email: str
    role: UserRole
    created_at: datetime


class StaffAccountLinkDTO(BaseModel):
    """User-Employee link DTO - replaces tuple[User, Employee]."""
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    employee_id: int
    full_name: str
    role: UserRole
    is_active: bool
    phone: str
