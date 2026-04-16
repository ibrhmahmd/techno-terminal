"""
StudentSummaryDTO - Immutable summary row for student listings.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass(frozen=True)
class StudentSummaryDTO:
    """Immutable summary row — used internally between services."""
    id: int
    full_name: str
    phone: Optional[str]
    gender: Optional[str]
    status: str
    is_active: bool
    current_group_id: Optional[int]
    current_group_name: Optional[str]
    date_of_birth: Optional[date]
