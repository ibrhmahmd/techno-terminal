"""
app/api/schemas/crm/student.py
────────────────────────────────
Public-facing (API boundary) Student DTOs.

These are intentionally separate from the domain schemas in
app/modules/crm/schemas/ — they define what API consumers see,
not what services accept internally.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class StudentPublic(BaseModel):
    """
    Full student profile returned by GET /crm/students/{id}.
    Safe for external clients — no internal keys, no audit metadata.
    """

    id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def convert_datetime_to_date(cls, v):
        """Convert datetime to date if needed (handles DB datetime fields)."""
        if isinstance(v, datetime):
            return v.date()
        return v


class StudentListItem(BaseModel):
    """
    Slim representation used in paginated list responses
    GET /crm/students — avoids sending unnecessary data on large lists.
    """

    id: int
    full_name: str
    phone: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
