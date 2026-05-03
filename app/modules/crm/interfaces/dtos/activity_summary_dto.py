"""
app/modules/crm/interfaces/dtos/activity_summary_dto.py
──────────────────────────────────────────────────────
Activity summary statistics DTO.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass(frozen=True)
class ActivitySummaryDTO:
    """Immutable DTO for activity summary statistics."""
    student_id: int
    total_activities: int
    activities_by_type: Dict[str, int] #TODO remove Dict and write a typed DTO class
    first_activity_date: Optional[datetime]
    last_activity_date: Optional[datetime]
