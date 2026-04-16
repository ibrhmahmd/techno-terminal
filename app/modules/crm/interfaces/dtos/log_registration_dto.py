"""
app/modules/crm/interfaces/dtos/log_registration_dto.py
───────────────────────────────────────────────────────
DTO for student registration activity logging.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogRegistrationDTO:
    """Immutable DTO for logging student registration."""
    student_id: int
    student_name: str
    performed_by: Optional[int] = None
