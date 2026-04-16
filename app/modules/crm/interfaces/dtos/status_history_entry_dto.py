"""
StatusHistoryEntryDTO - Status change audit entry.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class StatusHistoryEntryDTO:
    """Status history entry for audit trail."""
    id: int
    student_id: int
    previous_status: Optional[str]
    new_status: str
    changed_by_user_id: Optional[int]
    changed_by_name: Optional[str]
    notes: Optional[str]
    created_at: datetime
