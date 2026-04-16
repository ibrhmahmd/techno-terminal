"""
app/api/schemas/crm/history.py
──────────────────────────────
Pydantic schemas for student history and activity requests (CRM module).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ActivityLogRequest(BaseModel):
    """Request to log a manual activity."""
    activity_type: str
    activity_subtype: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: str
    metadata: Optional[Dict[str, Any]] = None


class EnrollmentHistoryEntry(BaseModel):
    """DTO for enrollment history entry."""
    id: int
    student_id: int
    enrollment_id: Optional[int] = None
    group_id: Optional[int] = None
    level_number: Optional[int] = None
    action: str
    action_date: datetime
    previous_group_id: Optional[int] = None
    previous_level_number: Optional[int] = None
    amount_due: Optional[float] = None
    amount_paid: Optional[float] = None
    final_status: Optional[str] = None
    notes: Optional[str] = None


class ActivitySummaryItem(BaseModel):
    """DTO for activity summary by type."""
    activity_type: str
    count: int


class ActivitySearchParams(BaseModel):
    """Parameters for searching activities."""
    search_term: Optional[str] = None
    activity_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    performed_by: Optional[int] = None
    student_id: Optional[int] = None
    limit: int = 50
