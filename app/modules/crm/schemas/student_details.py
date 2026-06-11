from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ParentInfo(BaseModel):
    id: int
    full_name: str
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    is_primary: bool = False

    model_config = {"from_attributes": True}


class EnrollmentInfo(BaseModel):
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
    total_due: float = 0.0
    total_discounts: float = 0.0
    total_paid: float = 0.0
    net_balance: float = 0.0
    enrollment_count: int = 0
    unpaid_enrollments: int = 0

    model_config = {"from_attributes": True}


class CurrentEnrollmentInfo(BaseModel):
    group_id: int
    group_name: str
    course_id: int
    course_name: str
    level_number: int
    instructor_name: Optional[str] = None
    enrollment_id: int

    model_config = {"from_attributes": True}


class StudentWithDetails(BaseModel):
    id: int
    full_name: str
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    status: str
    is_active: bool = True
    school_name: Optional[str] = None

    waiting_since: Optional[datetime] = None
    waiting_priority: Optional[int] = None
    waiting_notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    primary_parent: Optional[ParentInfo] = None
    enrollments: List[EnrollmentInfo] = Field(default_factory=list)

    current_enrollment: Optional[CurrentEnrollmentInfo] = None

    sessions_attended_count: int = 0
    sessions_absent_count: int = 0
    last_session_attended: Optional[datetime] = None

    enrollment_attendance: List["StudentEnrollmentAttendanceItem"] = Field(default_factory=list)

    balance_summary: StudentBalanceSummary = Field(default_factory=StudentBalanceSummary)

    siblings: List["SiblingInfo"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SiblingInfo(BaseModel):
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
    session_date: date
    status: str

    model_config = {"from_attributes": True}


class StudentEnrollmentAttendanceItem(BaseModel):
    enrollment_id: int
    group_id: int
    group_name: str
    course_name: str
    level_number: int
    present_count: int
    absent_count: int
    sessions: List[SessionAttendanceItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


StudentWithDetails.model_rebuild()
