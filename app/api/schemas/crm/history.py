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
    group_name: Optional[str] = None
    level_number: Optional[int] = None
    enrollment_status: Optional[str] = None
    action: str
    action_date: datetime
    previous_group_id: Optional[int] = None
    previous_level_number: Optional[int] = None
    previous_status: Optional[str] = None
    amount_due: Optional[float] = None
    discount_applied: Optional[float] = None
    transfer_reason: Optional[str] = None
    performed_by: Optional[int] = None
    performed_by_name: Optional[str] = None
    notes: Optional[str] = None


class StatusHistoryEntry(BaseModel):
    """DTO for status change history entry."""
    id: int
    student_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_at: datetime
    changed_by: Optional[int] = None
    changed_by_name: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class CompetitionHistoryEntry(BaseModel):
    """DTO for competition participation history entry."""
    id: int
    student_id: int
    competition_id: int
    competition_name: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    participation_type: str
    registration_date: Optional[datetime] = None
    subscription_amount: Optional[float] = None
    subscription_paid: Optional[bool] = None
    payment_id: Optional[int] = None
    result_position: Optional[int] = None
    result_notes: Optional[str] = None
    performed_by: Optional[int] = None
    performed_by_name: Optional[str] = None
    created_at: datetime


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
