"""
app/api/schemas/crm/student_details.py
────────────────────────────────────────
DTOs for student detail endpoint with full relationships.
"""
from datetime import date, datetime
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


class CurrentEnrollmentInfo(BaseModel):
    """Current active enrollment with group, course, and instructor details."""
    group_id: int
    group_name: str
    course_id: int
    course_name: str
    level_number: int
    instructor_name: Optional[str] = None
    enrollment_id: int

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
    school_name: Optional[str] = None  # From profile_metadata
    
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
    
    # Current enrollment (if active)
    current_enrollment: Optional[CurrentEnrollmentInfo] = None
    
    # Attendance summary (totals across all enrollments)
    sessions_attended_count: int = 0
    sessions_absent_count: int = 0
    last_session_attended: Optional[datetime] = None

    # Per-enrollment attendance with all session records
    enrollment_attendance: List["StudentEnrollmentAttendanceItem"] = Field(default_factory=list)
    
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


class SessionAttendanceItem(BaseModel):
    """Single session attendance record for API response."""
    session_date: date
    status: str

    model_config = {"from_attributes": True}


class StudentEnrollmentAttendanceItem(BaseModel):
    """
    Per-enrollment attendance summary with all session records.
    Included in StudentWithDetails for complete attendance history.
    """
    enrollment_id: int
    group_id: int
    group_name: str
    course_name: str
    level_number: int
    present_count: int
    absent_count: int
    sessions: List[SessionAttendanceItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# Update forward references
StudentWithDetails.model_rebuild()
