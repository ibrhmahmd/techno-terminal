"""
app/modules/crm/crm_schemas.py
───────────────────────────────
Typed input DTOs for the CRM service layer.

Usage in service:
    from app.modules.crm.crm_schemas import RegisterGuardianInput
    def register_guardian(data: RegisterGuardianInput | dict) -> Guardian: ...

Usage in FastAPI:
    @router.post("/guardians")
    async def create_guardian(data: RegisterGuardianInput): ...
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator
from app.shared.validators import validate_phone


class RegisterGuardianInput(BaseModel):
    """Input for crm_service.register_guardian() and find_or_create_guardian()."""
    full_name: str
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("phone_primary", mode="before")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        """Strip non-digits and enforce ≥10 digit minimum."""
        return validate_phone(v)


class RegisterStudentInput(BaseModel):
    """Input for crm_service.register_student()."""

    full_name: str
    # Streamlit date_input returns datetime.date; APIs may send ISO date strings.
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
