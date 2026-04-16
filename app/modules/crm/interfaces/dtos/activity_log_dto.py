"""
app/modules/crm/interfaces/dtos/activity_log_dto.py
─────────────────────────────────────────────────
Activity Log DTO for immutable activity data transfer.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class ActivityLogDTO:
    """Immutable DTO for activity log entries."""
    id: int
    student_id: int
    activity_type: str
    activity_subtype: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[int]
    description: str
    metadata: Dict[str, Any]
    performed_by: Optional[int]
    performed_by_name: Optional[str]
    created_at: datetime
