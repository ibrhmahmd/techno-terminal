"""
Employee Account API Schemas.

Request/response schemas for employee account creation.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class CreateEmployeeAccountRequest(BaseModel):
    """Request body for creating an employee account."""
    email: EmailStr = Field(..., description="Account email address")
    password: str = Field(..., min_length=8, description="Account password (min 8 characters)")
    role: Literal["admin", "system_admin"] = Field(..., description="User role")


class EmployeeAccountResponse(BaseModel):
    """Response for created employee account."""
    employee_id: int = Field(..., description="Employee ID")
    user_id: int = Field(..., description="Created user ID")
    email: str = Field(..., description="Account email")
    role: str = Field(..., description="Assigned role")
    created_at: datetime = Field(..., description="Account creation timestamp")
