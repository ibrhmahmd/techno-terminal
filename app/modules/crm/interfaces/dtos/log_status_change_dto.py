"""
app/modules/crm/interfaces/dtos/log_status_change_dto.py
────────────────────────────────────────────────────────
DTO for logging student status changes.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogStatusChangeDTO:
    """Immutable DTO for logging student status change."""
    student_id: int
    old_status: str
    new_status: str
    performed_by: Optional[int] = None
