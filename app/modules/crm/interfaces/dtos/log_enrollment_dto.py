"""
app/modules/crm/interfaces/dtos/log_enrollment_dto.py
─────────────────────────────────────────────────────
DTO for logging student enrollment activities.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogEnrollmentDTO:
    """Immutable DTO for logging student enrollment."""
    student_id: int
    enrollment_id: int
    group_id: int
    group_name: str
    level_number: int
    performed_by: Optional[int] = None
