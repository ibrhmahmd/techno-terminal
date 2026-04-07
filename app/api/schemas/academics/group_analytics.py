"""
app/api/schemas/academics/group_analytics.py
───────────────────────────────────────────
DTOs for group analytics and history endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# Level History DTOs
# ════════════════════════════════════════════════════════════

class GroupLevelHistoryItemDTO(BaseModel):
    """Individual level snapshot with student count."""
    level_id: int
    level_number: int
    status: str  # active, completed, cancelled
    course_id: int
    course_name: str
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    sessions_planned: int
    sessions_completed: int = 0  # calculated from attendance
    student_count: int = 0  # enrollments at this level
    effective_from: datetime
    effective_to: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GroupLevelHistoryResponseDTO(BaseModel):
    """Complete level progression history for a group."""
    group_id: int
    group_name: str
    total_levels: int
    completed_levels: int
    active_level: Optional[int] = None
    levels: list[GroupLevelHistoryItemDTO]


# ════════════════════════════════════════════════════════════
# Enrollment History DTOs
# ════════════════════════════════════════════════════════════

class EnrollmentHistoryItemDTO(BaseModel):
    """Individual enrollment with student and payment details."""
    enrollment_id: int
    student_id: int
    student_name: str
    student_phone: Optional[str] = None
    level_number_at_enrollment: int
    enrolled_at: Optional[datetime] = None
    status: str
    amount_due: float = 0.0
    discount_applied: float = 0.0
    payments_made: float = 0.0  # calculated from payments
    balance_remaining: float = 0.0

    model_config = {"from_attributes": True}


class GroupEnrollmentHistoryResponseDTO(BaseModel):
    """Complete enrollment history for a group."""
    group_id: int
    group_name: str
    total_enrollments: int
    active_enrollments: int
    completed_enrollments: int
    dropped_enrollments: int
    enrollments: list[EnrollmentHistoryItemDTO]


# ════════════════════════════════════════════════════════════
# Competition History DTOs
# ════════════════════════════════════════════════════════════

class CompetitionHistoryItemDTO(BaseModel):
    """Individual competition participation record."""
    participation_id: int
    competition_id: int
    competition_name: str
    team_id: int
    team_name: str
    category_name: Optional[str] = None
    entered_at: datetime
    left_at: Optional[datetime] = None
    is_active: bool
    final_placement: Optional[int] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class GroupCompetitionHistoryResponseDTO(BaseModel):
    """Complete competition participation history."""
    group_id: int
    group_name: str
    total_participations: int
    active_participations: int
    completed_participations: int
    competitions: list[CompetitionHistoryItemDTO]


# ════════════════════════════════════════════════════════════
# Instructor History DTOs
# ════════════════════════════════════════════════════════════

class InstructorHistoryItemDTO(BaseModel):
    """Individual instructor assignment summary."""
    instructor_id: int
    instructor_name: str
    is_current: bool = False
    levels_taught_count: int
    first_assigned_at: datetime
    last_assigned_at: datetime

    model_config = {"from_attributes": True}


class GroupInstructorHistoryResponseDTO(BaseModel):
    """Complete instructor assignment history."""
    group_id: int
    group_name: str
    total_instructors: int
    current_instructor: Optional[InstructorHistoryItemDTO] = None
    instructors: list[InstructorHistoryItemDTO]
