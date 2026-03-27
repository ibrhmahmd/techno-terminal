"""
app/modules/crm/schemas/guardian_schemas.py
────────────────────────────────────────────
Pydantic DTOs scoped to Guardian operations.
"""
from typing import Optional

from pydantic import BaseModel, field_validator
from app.shared.validators import validate_phone


class RegisterGuardianInput(BaseModel):
    """
    Input for CRMService.register_guardian() and find_or_create_guardian().
    The phone_primary field is validated and normalised on input.
    """
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


class UpdateGuardianDTO(BaseModel):
    """
    Input for CRMService.update_guardian().
    All fields are optional; only provided fields will be written.
    """
    full_name: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None
