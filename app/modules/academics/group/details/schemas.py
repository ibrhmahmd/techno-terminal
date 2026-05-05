"""
app/modules/academics/schemas/group_details_schemas.py
───────────────────────────────────────────────────────
Typed DTOs for Group Details API endpoints.

Follows dashboard API patterns with lookup tables and strict typing.
"""
from typing import Optional
from pydantic import BaseModel


# ═══════════════════════════════════════════════════════════════════════════════
# Lookup Table DTOs
# ═══════════════════════════════════════════════════════════════════════════════

class CourseLookupDTO(BaseModel):
    """Course entry for lookup table (course_id -> CourseInfo)."""
    course_id: int
    course_name: str


class InstructorLookupDTO(BaseModel):
    """Instructor entry for lookup table (instructor_id -> InstructorInfo)."""
    instructor_id: int
    instructor_name: str


class StudentLookupDTO(BaseModel):
    """Student entry for lookup table (student_id -> StudentInfo)."""
    student_id: int
    student_name: str
    phone: Optional[str] = None
    parent_name: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Stats DTOs (replace dict returns)
# ═══════════════════════════════════════════════════════════════════════════════

class EnrollmentStatsDTO(BaseModel):
    """Enrollment statistics per level."""
    total: int = 0
    completed: int = 0
    dropped: int = 0


class PaymentStatsDTO(BaseModel):
    """Payment statistics per level."""
    expected: float = 0.0
    collected: float = 0.0
    due: float = 0.0
    unpaid_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE Level Response DTO
# ═══════════════════════════════════════════════════════════════════════════════

class LevelDeleteResultDTO(BaseModel):
    """Response after soft-deleting a level."""
    level_id: int
    level_number: int
    group_id: int
    deleted_at: str  # ISO 8601 timestamp


# ═══════════════════════════════════════════════════════════════════════════════
# Session DTOs
# ═══════════════════════════════════════════════════════════════════════════════

class SessionInLevelDTO(BaseModel):
    """Session within a level context."""
    session_id: int
    session_number: int
    date: str  # YYYY-MM-DD
    time_start: str  # HH:MM
    time_end: str  # HH:MM
    status: str  # 'scheduled' | 'completed' | 'cancelled'
    is_extra_session: bool
    actual_instructor_id: Optional[int] = None
    is_substitute: bool


# ═══════════════════════════════════════════════════════════════════════════════
# Level with Sessions DTOs (GET /levels/detailed)
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentSummaryDTO(BaseModel):
    """Payment aggregation for a level."""
    total_expected: float
    total_collected: float
    total_due: float
    collection_rate: float  # 0.0 - 1.0
    unpaid_students_count: int


class LevelWithSessionsDTO(BaseModel):
    """Level data with embedded sessions and stats."""
    level_number: int
    level_id: int
    course_id: int
    instructor_id: int
    status: str  # 'active' | 'completed' | 'cancelled'
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD
    
    sessions: list[SessionInLevelDTO]
    
    students_count: int
    students_completed: int
    students_dropped: int
    
    payment_summary: PaymentSummaryDTO


class GroupLevelsDetailedResponseDTO(BaseModel):
    """Root response for GET /academics/groups/{id}/levels/detailed"""
    group_id: int
    generated_at: str  # ISO 8601 timestamp
    cache_ttl: int
    
    # Lookup tables
    courses: dict[int, CourseLookupDTO]
    instructors: dict[int, InstructorLookupDTO]
    
    # Levels with sessions
    levels: list[LevelWithSessionsDTO]


# ═══════════════════════════════════════════════════════════════════════════════
# Attendance Grid DTOs (GET /attendance)
# ═══════════════════════════════════════════════════════════════════════════════

class AttendanceRosterStudentDTO(BaseModel):
    """Student entry in attendance roster."""
    student_id: int
    student_name: str
    enrollment_id: int
    billing_status: str  # 'paid' | 'due'
    joined_at: Optional[str] = None  # ISO 8601


class AttendanceSessionDTO(BaseModel):
    """Session with attendance map for grid display."""
    session_id: int
    session_number: int
    date: str  # YYYY-MM-DD
    time_start: str  # HH:MM
    time_end: str  # HH:MM
    status: str  # 'scheduled' | 'completed' | 'cancelled'
    is_extra_session: bool
    # Map of student_id -> attendance status for O(1) lookup
    attendance: dict[int, Optional[str]]  # student_id -> 'present'|'absent'|'excused'|'late'|None


class GroupAttendanceResponseDTO(BaseModel):
    """Root response for GET /academics/groups/{id}/attendance"""
    group_id: int
    level_number: int
    generated_at: str
    cache_ttl: int
    
    # Students enrolled in this level
    roster: list[AttendanceRosterStudentDTO]
    
    # Sessions with attendance map
    sessions: list[AttendanceSessionDTO]


# ═══════════════════════════════════════════════════════════════════════════════
# Finance / Payments DTOs (GET /finance/groups/{id}/payments)
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentInLevelDTO(BaseModel):
    """Individual payment record within a level."""
    payment_id: int
    student_id: int
    student_name: str
    amount: float
    discount_amount: float
    payment_date: str  # YYYY-MM-DD
    payment_method: str  # 'cash' | 'card' | 'bank_transfer' | 'wallet'
    status: str  # 'completed' | 'pending' | 'failed' | 'refunded'
    receipt_number: Optional[str] = None
    transaction_type: str  # 'payment' | 'refund' | 'adjustment'


class LevelPaymentSummaryDTO(BaseModel):
    """Payment summary for a single level."""
    level_number: int
    level_status: str
    course_name: str
    expected: float
    collected: float
    due: float
    total_students: int
    paid_count: int
    unpaid_count: int
    payments: list[PaymentInLevelDTO]


class GroupPaymentsSummaryDTO(BaseModel):
    """Overall payment summary across all levels."""
    total_expected_all_levels: float
    total_collected_all_levels: float
    total_due_all_levels: float
    collection_rate: float


class GroupPaymentsResponseDTO(BaseModel):
    """Root response for GET /finance/groups/{id}/payments"""
    group_id: int
    generated_at: str
    cache_ttl: int
    
    summary: GroupPaymentsSummaryDTO
    by_level: list[LevelPaymentSummaryDTO]


# ═══════════════════════════════════════════════════════════════════════════════
# Enrollments / Students DTOs (GET /enrollments/all)
# ═══════════════════════════════════════════════════════════════════════════════

class EnrollmentInLevelDTO(BaseModel):
    """Enrollment record with computed stats for display."""
    enrollment_id: int
    student_id: int
    status: str  # 'active' | 'completed' | 'dropped'
    enrolled_at: str
    dropped_at: Optional[str] = None
    sessions_attended: int
    sessions_total: int
    payment_status: str  # 'paid' | 'due' | 'partial'
    amount_due: float
    amount_paid: float
    discount_applied: float
    can_transfer: bool
    can_drop: bool


class LevelEnrollmentSummaryDTO(BaseModel):
    """Summary stats for enrollments in a level."""
    total: int
    active: int
    completed: int
    dropped: int
    paid: int
    unpaid: int


class LevelWithEnrollmentsDTO(BaseModel):
    """Level with its enrollments and summary."""
    level_number: int
    level_status: str
    course_name: str
    enrollments: list[EnrollmentInLevelDTO]
    summary: LevelEnrollmentSummaryDTO


class TransferOptionDTO(BaseModel):
    """Available group for student transfer."""
    group_id: int
    group_name: str
    course_name: str
    available_slots: int


class GroupEnrollmentsResponseDTO(BaseModel):
    """Root response for GET /academics/groups/{id}/enrollments/all"""
    group_id: int
    generated_at: str
    cache_ttl: int
    
    # Lookup table
    students: dict[int, StudentLookupDTO]
    
    # Enrollments grouped by level
    grouped_by_level: list[LevelWithEnrollmentsDTO]
    
    # For transfer dropdown
    transfer_options: list[TransferOptionDTO]
