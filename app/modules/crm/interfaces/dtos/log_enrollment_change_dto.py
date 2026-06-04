"""
app/modules/crm/interfaces/dtos/log_enrollment_change_dto.py
───────────────────────────────────────────────────────────
DTO for logging enrollment lifecycle changes.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogEnrollmentChangeDTO:
    """Immutable DTO for logging enrollment changes (transfer, cancel, complete, financials_updated, dropped)."""
    student_id: int
    enrollment_id: int
    action: str  # 'transferred', 'cancelled', 'completed', 'reinstated', 'financials_updated', 'dropped'
    old_group_id: Optional[int] = None
    new_group_id: Optional[int] = None
    changes_summary: Optional[str] = None
    performed_by: Optional[int] = None
