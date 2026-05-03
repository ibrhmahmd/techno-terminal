"""
app/modules/crm/models/activity_models.py
────────────────────────────────────────
Activity and history tracking models for comprehensive student audit trails.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


# ── Student Activity Log ───────────────────────────────────────────────────

class StudentActivityLogBase(SQLModel):
    """Base model for student activity logging."""
    activity_type: str  # 'enrollment', 'payment', 'group_change', 'competition', 'status_change', 'note', 'communication'
    activity_subtype: Optional[str] = None  # 'enrollment_created', 'payment_received', 'group_transferred', etc.
    reference_type: Optional[str] = None  # 'enrollment', 'payment', 'group', 'competition', 'team'
    reference_id: Optional[int] = None
    description: str
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=SAColumn("meta", JSONB)
    )
    created_at: Optional[datetime] = None


class StudentActivityLog(StudentActivityLogBase, table=True):
    """Append-only activity log for all student actions."""
    __tablename__ = "student_activity_log"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    performed_by: Optional[int] = Field(default=None, foreign_key="users.id")


class StudentActivityLogRead(StudentActivityLogBase):
    """DTO for reading activity log entries."""
    id: int
    student_id: int
    performed_by: Optional[int] = None
    performed_by_name: Optional[str] = None  # Enriched field


class StudentActivityLogCreate(SQLModel):
    """DTO for creating activity log entry."""
    student_id: int
    activity_type: str
    activity_subtype: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: str
    meta: Optional[Dict[str, Any]] = None
    performed_by: Optional[int] = None


# ── DTOs for Activity Queries ─────────────────────────────────────────────

class ActivityTimelineFilter(SQLModel):
    """Filter parameters for activity timeline queries."""
    student_id: Optional[int] = None
    activity_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    performed_by: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    skip: int = 0
    limit: int = 50


class StudentActivitySummary(SQLModel):
    """Summary of student activities."""
    student_id: int
    total_activities: int 
    activities_by_type: dict[str, int]#TODO remove Dict and write a typed DTO class
    first_activity_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None


class EnrollmentTimelineEntry(SQLModel):
    """Single entry in enrollment timeline."""
    date: datetime
    action: str
    group_name: Optional[str] = None
    level_number: Optional[int] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class StudentEnrollmentTimeline(SQLModel):
    """Complete enrollment timeline for a student."""
    student_id: int
    student_name: str
    timeline: List[EnrollmentTimelineEntry]
