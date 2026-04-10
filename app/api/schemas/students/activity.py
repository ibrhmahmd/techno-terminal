"""
app/api/schemas/students/activity.py
─────────────────────────────────────
Activity log and history-related DTOs.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ActivityActorDTO(BaseModel):
    """Information about who performed an activity."""
    user_id: int = Field(..., description="User ID of the actor")
    name: Optional[str] = Field(None, description="Display name of the actor")
    role: Optional[str] = Field(None, description="Role of the actor")
    
    model_config = {"from_attributes": True}


class ActivityReferenceDTO(BaseModel):
    """Reference to related entity (enrollment, payment, etc.)."""
    reference_type: str = Field(..., description="Type of entity (enrollment, payment, etc.)")
    reference_id: int = Field(..., description="ID of the referenced entity")
    reference_name: Optional[str] = Field(None, description="Human-readable name/description")
    
    model_config = {"from_attributes": True}


class ActivityLogResponseDTO(BaseModel):
    """Structured activity log record."""
    activity_id: int = Field(..., description="Unique activity record ID")
    student_id: int = Field(..., description="Student ID the activity relates to")
    activity_type: str = Field(..., description="Category of activity (enrollment, payment, etc.)")
    activity_subtype: Optional[str] = Field(None, description="Specific subtype")
    description: str = Field(..., description="Human-readable description")
    reference: Optional[ActivityReferenceDTO] = Field(None, description="Related entity reference")
    performed_by: Optional[ActivityActorDTO] = Field(None, description="Who performed the action")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional structured metadata")
    created_at: datetime = Field(..., description="When the activity occurred")
    
    model_config = {"from_attributes": True}


class ActivitySearchResultDTO(BaseModel):
    """Result container for activity search."""
    activities: List[ActivityLogResponseDTO] = Field(..., description="List of matching activities")
    total_count: int = Field(..., description="Total matching activities")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Items per page")
    has_more: bool = Field(..., description="Whether more results are available")
    
    model_config = {"from_attributes": True}


class ActivityTypeSummaryDTO(BaseModel):
    """Summary of activities by type."""
    activity_type: str = Field(..., description="Type of activity")
    count: int = Field(..., description="Number of activities of this type")
    last_occurrence: Optional[datetime] = Field(None, description="Most recent activity timestamp")
    
    model_config = {"from_attributes": True}


class ActivityTimelineResponseDTO(BaseModel):
    """Activity timeline for a student."""
    student_id: int = Field(..., description="Student ID")
    start_date: datetime = Field(..., description="Timeline start date")
    end_date: datetime = Field(..., description="Timeline end date")
    activities: List[ActivityLogResponseDTO] = Field(..., description="Activities in the timeline")
    summary_by_type: List[ActivityTypeSummaryDTO] = Field(..., description="Summary grouped by activity type")
    
    model_config = {"from_attributes": True}


class ActivitySearchResultItemDTO(BaseModel):
    """Individual activity search result item."""
    activity_id: int = Field(..., description="Unique activity record ID")
    student_id: int = Field(..., description="Student ID the activity relates to")
    activity_type: str = Field(..., description="Category of activity")
    description: str = Field(..., description="Human-readable description")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional structured metadata")
    created_at: Optional[str] = Field(None, description="ISO format timestamp")
    
    model_config = {"from_attributes": True}


class RecentActivityItemDTO(BaseModel):
    """Recent activity summary item."""
    activity_id: int = Field(..., description="Unique activity record ID")
    student_id: int = Field(..., description="Student ID")
    activity_type: str = Field(..., description="Category of activity")
    description: str = Field(..., description="Human-readable description")
    created_at: Optional[str] = Field(None, description="ISO format timestamp")
    performed_by_name: Optional[str] = Field(None, description="Name of user who performed the action")
    
    model_config = {"from_attributes": True}


class ManualActivityResponseDTO(BaseModel):
    """Response for manually logged activity."""
    activity_id: int = Field(..., description="Unique activity record ID")
    student_id: int = Field(..., description="Student ID")
    activity_type: str = Field(..., description="Category of activity")
    description: str = Field(..., description="Human-readable description")
    created_at: Optional[str] = Field(None, description="ISO format timestamp")
    
    model_config = {"from_attributes": True}


class StudentHistoryItemDTO(BaseModel):
    """Individual student history item wrapper."""
    item_type: str = Field(..., description="Type of history item")
    data: Dict[str, Any] = Field(..., description="History data payload")
    
    model_config = {"from_attributes": True}


class ActivityTimelineItemDTO(BaseModel):
    """Individual activity timeline item."""
    activity_id: int = Field(..., description="Unique activity record ID")
    item_type: str = Field(..., description="Type of item (activity)")
    activity_type: str = Field(..., description="Category of activity")
    created_at: Optional[str] = Field(None, description="ISO format timestamp")
    
    model_config = {"from_attributes": True}
