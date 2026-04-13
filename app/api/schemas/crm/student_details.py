"""
app/api/schemas/crm/student_details.py
────────────────────────────────────────
DTOs for student detail endpoint with full relationships.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ParentInfo(BaseModel):
    """Simplified parent info for student details response."""
    id: int
    full_name: str
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    is_primary: bool = False

    model_config = {"from_attributes": True}


class EnrollmentInfo(BaseModel):
    """Enrollment with group and course info."""
    enrollment_id: int
    group_id: int
    group_name: str
    course_id: int
    course_name: str
    level_number: int
    status: str
    amount_due: Optional[float] = None
    discount_applied: float = 0.0
    enrolled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StudentBalanceSummary(BaseModel):
    """Aggregated balance summary for a student."""
    total_due: float = 0.0
    total_discounts: float = 0.0
    total_paid: float = 0.0
    net_balance: float = 0.0  # Positive = credit, Negative = debt
    enrollment_count: int = 0
    unpaid_enrollments: int = 0

    model_config = {"from_attributes": True}


class StudentWithDetails(BaseModel):
    """
    Complete student profile with relationships and balance summary.
    Used by GET /crm/students/{id}/details
    """
    # Core student fields
    id: int
    full_name: str
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None  # Computed from date_of_birth
    gender: Optional[str] = None  # Computed from date_of_birth
    phone: Optional[str] = None
    notes: Optional[str] = None
    status: str
    is_active: bool = True
    
    # Waiting list metadata
    waiting_since: Optional[datetime] = None
    waiting_priority: Optional[int] = None
    waiting_notes: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relationships
    primary_parent: Optional[ParentInfo] = None
    enrollments: List[EnrollmentInfo] = Field(default_factory=list)
    
    # Financial summary
    balance_summary: StudentBalanceSummary = Field(default_factory=StudentBalanceSummary)
    
    # Siblings (optional inclusion)
    siblings: List["SiblingInfo"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SiblingInfo(BaseModel):
    """
    Sibling student information.
    Used by GET /students/{id}/siblings and included in StudentWithDetails.
    """
    student_id: int
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    status: str
    parent_id: int
    parent_name: str
    enrollments_count: int = 0

    model_config = {"from_attributes": True}


# Update forward reference
StudentWithDetails.model_rebuild()
