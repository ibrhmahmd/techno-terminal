"""Employee Schemas

Pydantic DTOs for employee CRUD operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.hr.constants import EmploymentType


class CreateEmployeeDTO(BaseModel):
    """Complete DTO for creating an employee."""
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\d{10,}$")
    email: Optional[str] = Field(None, max_length=255)
    national_id: str = Field(..., min_length=10, max_length=20)
    university: str = Field(..., min_length=1, max_length=100)
    major: str = Field(..., min_length=1, max_length=100)
    is_graduate: bool = False
    job_title: Optional[str] = Field(None, max_length=100)
    employment_type: EmploymentType = "full_time"
    monthly_salary: Optional[Decimal] = None
    contract_percentage: Optional[float] = None
    is_active: bool = True

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        """Strip non-digits from phone."""
        return "".join(c for c in v if c.isdigit())


class UpdateEmployeeDTO(BaseModel):
    """Partial update DTO - all fields optional."""
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\d{10,}$")
    email: Optional[str] = Field(None, max_length=255)
    national_id: Optional[str] = Field(None, min_length=10, max_length=20)
    university: Optional[str] = Field(None, min_length=1, max_length=100)
    major: Optional[str] = Field(None, min_length=1, max_length=100)
    is_graduate: Optional[bool] = None
    job_title: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[EmploymentType] = None
    monthly_salary: Optional[Decimal] = None
    contract_percentage: Optional[float] = None
    is_active: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return "".join(c for c in v if c.isdigit())


class EmployeeReadDTO(BaseModel):
    """Employee data returned by services."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    national_id: str
    university: str
    major: str
    is_graduate: bool
    job_title: Optional[str] = None
    employment_type: EmploymentType
    monthly_salary: Optional[Decimal] = None
    contract_percentage: Optional[float] = None
    is_active: bool
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = None
