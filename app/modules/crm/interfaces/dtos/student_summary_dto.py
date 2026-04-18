"""
StudentSummaryDTO - Immutable summary row for student listings.
"""
from typing import Optional
from datetime import date
from pydantic import BaseModel


class StudentSummaryDTO(BaseModel):
    """Immutable summary row — used internally between services."""
    model_config = {"frozen": True}

    id: int
    full_name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    status: str
    is_active: bool
    current_group_id: Optional[int] = None
    current_group_name: Optional[str] = None
    date_of_birth: Optional[date] = None
