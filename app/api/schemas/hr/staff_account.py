"""
app/api/schemas/hr/staff_account.py
───────────────────────────────────
Staff account related request/response schemas.

This module defines input/output DTOs for staff account management endpoints,
separating validation logic from route handling per SOLID principles.
"""
from pydantic import BaseModel

from app.api.schemas.hr.employee import EmployeeCreateInput


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
