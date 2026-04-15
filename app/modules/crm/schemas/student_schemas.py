"""
app/modules/crm/schemas/student_schemas.py
───────────────────────────────────────────
Pydantic DTOs scoped to Student operations.
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


from app.modules.crm.models.student_models import StudentStatus


class RegisterStudentDTO(BaseModel):
    """
    Input for CRMService.register_student().
    Streamlit date_input returns datetime.date; APIs may send ISO date strings.
    """
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # 'male' | 'female'
    phone: Optional[str] = None
    notes: Optional[str] = None
    # NEW: Optional status on registration (defaults to active)
    status: Optional[str] = "active"


class UpdateStudentDTO(BaseModel):
    """
    Input for CRMService.update_student().
    All fields are optional; only provided fields will be written.
    """
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None  # Deprecated but kept for compatibility
    status: Optional[StudentStatus] = None  # Strict enum validation


class StatusHistoryEntryDTO(BaseModel):
    """Typed audit entry in student status trail. Replaces list[dict]."""
    timestamp: datetime
    changed_by: Optional[int] = None
    old_status: Optional[str] = None
    new_status: str
    notes: Optional[str] = None
    action: Optional[str] = None       # e.g. "priority_change"
    new_priority: Optional[int] = None


# NEW DTO for status updates
class UpdateStudentStatusDTO(BaseModel):
    """Input for updating student status with audit notes."""
    status: StudentStatus
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes explaining the status change (e.g., 'Waiting for Level 2 group')"
    )


# NEW DTO for waiting list priority updates
class SetWaitingPriorityDTO(BaseModel):
    """Input for setting student priority on waiting list."""
    priority: int = Field(..., ge=1, le=1000, description="Priority number (1 = highest priority)")
    notes: Optional[str] = None


class StudentResponseDTO(BaseModel):
    """Output DTO for student data including status."""
    id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool  # Deprecated but kept for backward compatibility
    status: str  # NEW: Current status
    waiting_since: Optional[datetime] = None  # NEW
    waiting_priority: Optional[int] = None  # NEW
    waiting_notes: Optional[str] = None  # NEW
    status_history: list[StatusHistoryEntryDTO] = []  # NEW
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StudentStatusSummaryDTO(BaseModel):
    """Output DTO for student status counts."""
    total: int
    active: int
    waiting: int
    inactive: int


class RegisterStudentCommandDTO(BaseModel):
    """
    Unified command DTO encompassing the student payload, parent relationship,
    and audit context for full CQRS-style registration.
    """
    student_data: RegisterStudentDTO
    parent_id: Optional[int] = None
    relationship: Optional[str] = None
    created_by_user_id: Optional[int] = None
