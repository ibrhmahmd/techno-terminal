"""
app/modules/crm/interfaces/dtos/status_history_dto.py
─────────────────────────────────────────────────────
DTO for student status change history entries.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class StatusHistoryDTO:
    """Immutable DTO for status change history entries."""
    
    id: int
    student_id: int
    
    old_status: Optional[str]
    new_status: str
    
    changed_at: datetime
    changed_by: Optional[int]
    changed_by_name: Optional[str]
    
    reason: Optional[str]
    notes: Optional[str]
