"""
app/modules/crm/interfaces/dtos/log_competition_registration_dto.py
────────────────────────────────────────────────────────────────────
DTO for logging competition registration activities.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogCompetitionRegistrationDTO:
    """Immutable DTO for logging competition registration."""
    student_id: int
    competition_id: int
    competition_name: str
    performed_by: Optional[int] = None
