"""
HR module service DTOs.

Data Transfer Objects for HR service layer operations.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class CreateEmployeeAccountDTO(BaseModel):
    """Input DTO for creating employee account.
    
    Wraps all parameters required for creating a user account for an employee.
    """
    employee_id: int = Field(..., gt=0, description="Employee ID to link account to")
    email: EmailStr = Field(..., description="Account email address")
    password: str = Field(..., min_length=8, description="Account password (min 8 characters)")
    role: str = Field(..., pattern=r"^(admin|system_admin)$", description="User role: admin or system_admin")


class EmployeeAccountResultDTO(BaseModel):
    """Result DTO for created employee account.
    
    Returned after successfully creating an employee account.
    """
    employee_id: int = Field(..., description="Employee ID")
    user_id: int = Field(..., description="Created user ID")
    email: str = Field(..., description="Account email")
    role: str = Field(..., description="Assigned role")
    created_at: datetime = Field(..., description="Account creation timestamp")
