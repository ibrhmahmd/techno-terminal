"""
app/api/schemas/crm/activity.py
────────────────────────────────
Pydantic schemas for student activity and history (CRM module).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ActivityReferenceDTO(BaseModel):
    """Reference to related entity."""
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class ActivityActorDTO(BaseModel):
    """Actor who performed the activity."""
    user_id: Optional[int] = None
    user_name: Optional[str] = None


class ActivityLogResponseDTO(BaseModel):
    """DTO for activity log entry response."""
    activity_id: int
    student_id: int
    activity_type: str
    activity_subtype: Optional[str] = None
    description: str
    reference: Optional[ActivityReferenceDTO] = None
    performed_by: Optional[ActivityActorDTO] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class RecentActivityItemDTO(BaseModel):
    """DTO for recent activity list item."""
    activity_id: int
    student_id: int
    activity_type: str
    description: str
    created_at: Optional[str] = None
    performed_by_name: Optional[str] = None


class ManualActivityResponseDTO(BaseModel):
    """DTO for manual activity logging response."""
    activity_id: int
    student_id: int
    activity_type: str
    description: str
    created_at: Optional[str] = None


class ActivitySearchResultItemDTO(BaseModel):
    """DTO for activity search result."""
    activity_id: int
    student_id: int
    activity_type: str
    description: str
    meta: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
