"""
app/modules/crm/interfaces/dtos/timeline_filter_dto.py
──────────────────────────────────────────────────────
Filter parameters for activity timeline queries.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class TimelineFilterDTO:
    """Immutable DTO for filtering activity timeline queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    activity_types: Optional[List[str]] = None
    performed_by: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    skip: int = 0
    limit: int = 100
