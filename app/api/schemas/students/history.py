"""
app/api/schemas/students/history.py
───────────────────────────────────
Student activity and history tracking schemas.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ActivityLogRequest(BaseModel):
    """Request schema for logging activity."""
    activity_type: str
    activity_subtype: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: str
    metadata: Optional[dict] = None


class ActivityTimelineFilterParams(BaseModel):
    """Filter parameters for activity timeline."""
    activity_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    performed_by: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class EnrollmentHistoryEntry(BaseModel):
    """Response schema for enrollment history."""
    id: int
    student_id: int
    enrollment_id: Optional[int]
    group_id: Optional[int]
    level_number: Optional[int]
    action: str
    action_date: datetime
    previous_group_id: Optional[int]
    previous_level_number: Optional[int]
    amount_due: Optional[float]
    amount_paid: Optional[float]
    final_status: Optional[str]
    notes: Optional[str]


class ActivitySummaryItem(BaseModel):
    """Response schema for activity summary item."""
    activity_type: str
    count: int


class ActivitySearchParams(BaseModel):
    """Search parameters for activity search."""
    search_term: Optional[str] = None
    activity_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    performed_by: Optional[int] = None
    student_id: Optional[int] = None
    limit: int = 50
