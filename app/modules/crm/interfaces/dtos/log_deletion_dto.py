"""
app/modules/crm/interfaces/dtos/log_deletion_dto.py
───────────────────────────────────────────────────
DTO for logging student deletion activities.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogDeletionDTO:
    """Immutable DTO for logging student deletion."""
    student_id: int
    student_name: str
    performed_by: Optional[int] = None
