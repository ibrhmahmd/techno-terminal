"""
app/modules/crm/interfaces/dtos/log_note_added_dto.py
───────────────────────────────────────────────────────
DTO for logging note/communication activities.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogNoteAddedDTO:
    """Immutable DTO for logging note/communication activities."""
    student_id: int
    note_id: int
    note_type: str
    performed_by: Optional[int] = None
