"""
app/api/schemas/crm/history.py
──────────────────────────────
Pydantic schemas for student history and activity requests (CRM module).
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ActivityType(str, Enum):
    """Valid activity types for logging."""
    REGISTRATION = "registration"
    STATUS_CHANGE = "status_change"
    ENROLLMENT = "enrollment"
    ENROLLMENT_CHANGE = "enrollment_change"
    PAYMENT = "payment"
    NOTE_ADDED = "note_added"
    COMPETITION = "competition"
    DELETION = "deletion"


class ReferenceType(str, Enum):
    """Valid reference types for activities."""
    STUDENT = "student"
    ENROLLMENT = "enrollment"
    PAYMENT = "payment"
    GROUP = "group"
    COURSE = "course"
    COMPETITION = "competition"


class ActivityLogRequest(BaseModel):
    """Request to log a manual activity."""
    activity_type: ActivityType
    activity_subtype: Optional[str] = Field(None, max_length=50)
    reference_type: Optional[ReferenceType] = None
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
    activity_type: ActivityType
    count: int


class ActivitySearchParams(BaseModel):
    """Parameters for searching activities."""
    search_term: Optional[str] = Field(None, max_length=100)
    activity_types: Optional[List[ActivityType]] = Field(None, max_length=10)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    performed_by: Optional[int] = Field(None, gt=0)
    student_id: Optional[int] = Field(None, gt=0)
    limit: int = Field(50, ge=1, le=100)

    @validator("date_to")
    def validate_date_range(cls, v, values):
        if v and values.get("date_from") and v < values["date_from"]:
            raise ValueError("date_to must be after date_from")
        return v
