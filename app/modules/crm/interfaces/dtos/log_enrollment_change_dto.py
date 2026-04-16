"""
app/modules/crm/interfaces/dtos/log_enrollment_change_dto.py
───────────────────────────────────────────────────────────
DTO for logging enrollment lifecycle changes.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogEnrollmentChangeDTO:
    """Immutable DTO for logging enrollment changes (transfer, cancel, complete)."""
    student_id: int
    enrollment_id: int
    action: str  # 'transferred', 'cancelled', 'completed', 'reinstated'
    old_group_id: Optional[int] = None
    new_group_id: Optional[int] = None
    performed_by: Optional[int] = None
