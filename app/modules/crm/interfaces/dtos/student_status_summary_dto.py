"""
app/modules/crm/interfaces/dtos/student_status_summary_dto.py
───────────────────────────────────────────────────────────
Student status summary DTO.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentStatusSummaryDTO:
    """Summary counts of students by status."""
    total: int
    active: int
    inactive: int
