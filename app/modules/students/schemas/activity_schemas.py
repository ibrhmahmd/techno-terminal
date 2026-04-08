"""
app/modules/students/schemas/activity_schemas.py
────────────────────────────────────────────────
Request DTOs for student activity service layer.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class LogActivityRequestDTO(BaseModel):
    """Request DTO for logging a simple activity."""
    student_id: int = Field(..., description="Student ID the activity relates to")
    activity_type: str = Field(..., description="Category of activity")
    activity_subtype: Optional[str] = Field(None, description="Specific subtype")
    description: Optional[str] = Field(None, description="Human-readable description")
    reference_type: Optional[str] = Field(None, description="Type of related entity")
    reference_id: Optional[int] = Field(None, description="ID of related entity")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured metadata")
    performed_by: Optional[int] = Field(None, description="User ID who performed the action")
    created_at: Optional[datetime] = Field(None, description="Timestamp of activity")
    
    model_config = {"from_attributes": True}


class EnrollmentChangeRequestDTO(BaseModel):
    """Request DTO for logging enrollment changes."""
    student_id: int = Field(..., description="Student ID")
    enrollment_id: int = Field(..., description="Enrollment ID")
    action: str = Field(..., description="Action performed (enroll, drop, transfer)")
    group_id: int = Field(..., description="Target group ID")
    level_number: int = Field(..., description="Target level number")
    previous_group_id: Optional[int] = Field(None, description="Previous group ID (for transfers)")
    previous_level_number: Optional[int] = Field(None, description="Previous level number (for transfers)")
    amount_due: Optional[float] = Field(None, description="Amount due for enrollment")
    performed_by: Optional[int] = Field(None, description="User ID who performed the action")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    model_config = {"from_attributes": True}


class ActivitySearchRequestDTO(BaseModel):
    """Request DTO for searching activities."""
    search_term: Optional[str] = Field(None, description="Search term for filtering")
    activity_types: Optional[list[str]] = Field(None, description="List of activity types to filter")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    performed_by: Optional[int] = Field(None, description="Filter by user who performed action")
    student_id: Optional[int] = Field(None, description="Filter by student ID")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of results")
    
    model_config = {"from_attributes": True}


class ActivityFilterRequestDTO(BaseModel):
    """Request DTO for filtering activity logs."""
    student_id: Optional[int] = Field(None, description="Filter by student ID")
    activity_types: Optional[list[str]] = Field(None, description="List of activity types")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    reference_type: Optional[str] = Field(None, description="Filter by reference type")
    reference_id: Optional[int] = Field(None, description="Filter by reference ID")
    
    model_config = {"from_attributes": True}
