"""
app/modules/academics/schemas/scheduling_dtos.py
────────────────────────────────────────────────
DTOs for modular scheduling services.
These DTOs support the decomposed service architecture:
- GroupLevelService
- SessionService  
- GroupLifecycleService (orchestrator)
"""
from datetime import date, time
from decimal import Decimal
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, model_validator

from app.shared.constants import DEFAULT_SESSIONS_PER_LEVEL

WeekDay = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]


# ═══════════════════════════════════════════════════════════════════════════════
# Input DTOs
# ═══════════════════════════════════════════════════════════════════════════════

class CreateGroupDTO(BaseModel):
    """Input for creating a new group (simplified from ScheduleGroupInput)."""
    course_id: int
    instructor_id: int
    default_day: WeekDay
    default_time_start: time
    default_time_end: time
    max_capacity: int = 15
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_time_window(self) -> "CreateGroupDTO":
        """Reuse the module time window check (11AM–9PM)."""
        from app.modules.academics.helpers.time_helpers import validate_times
        validate_times(self.default_time_start, self.default_time_end)
        return self


class CreateGroupLevelDTO(BaseModel):
    """Input for creating a group level."""
    group_id: int
    level_number: int
    course_id: int
    instructor_id: Optional[int] = None
    sessions_planned: int = Field(default=DEFAULT_SESSIONS_PER_LEVEL)
    price_override: Optional[Decimal] = None
    start_date: Optional[date] = None
    status: str = "active"


class GenerateSessionsDTO(BaseModel):
    """Input for session generation."""
    group_id: int
    group_level_id: int  # NEW: Link sessions to levels
    level_number: int
    count: int
    start_date: date
    time_start: time
    time_end: time
    instructor_id: int


class ProgressLevelDTO(BaseModel):
    """Input for progressing to next level."""
    group_id: int
    price_override: Optional[Decimal] = None
    auto_migrate_enrollments: bool = True
    target_level: Optional[int] = None  # If None, defaults to current + 1
    complete_current_level: bool = True  # If False, keeps current level active
    instructor_id: Optional[int] = None  # Override group's default instructor
    session_start_date: Optional[date] = None  # Override default session start date
    course_id: Optional[int] = None  # Override group's course
    group_name: Optional[str] = None  # Override group name


class CreateGroupWithLevelDTO(BaseModel):
    """Input for creating group with first level."""
    group_input: CreateGroupDTO
    sessions_per_level: int = DEFAULT_SESSIONS_PER_LEVEL
    start_date: Optional[date] = None


class UpdateSessionInstructorDTO(BaseModel):
    """Input for updating session instructor."""
    session_id: int
    instructor_id: int
    is_substitute: bool = False


class CancelSessionDTO(BaseModel):
    """Input for canceling a session."""
    session_id: int
    reason: Optional[str] = None


class CompleteGroupLevelDTO(BaseModel):
    """Input for completing a group level."""
    group_id: int
    level_number: int
    completion_notes: Optional[str] = None


class MigrateEnrollmentsDTO(BaseModel):
    """Input for migrating enrollments between levels."""
    group_id: int
    from_level: int
    to_level: int
    price_override: Optional[Decimal] = None
    preserve_discounts: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# Output/Result DTOs
# ═══════════════════════════════════════════════════════════════════════════════

class GroupResult(BaseModel):
    """Output for single group operations."""
    group_id: int
    group_name: str
    message: Optional[str] = None


class GroupLevelResult(BaseModel):
    """Output for level creation."""
    level_id: int
    group_id: int
    level_number: int
    sessions_count: int
    status: str


class SessionGenerationResult(BaseModel):
    """Output for session generation."""
    sessions: List[dict]  # Serialized session data #TODO remove Dict and write a typed DTO class
    count: int
    group_id: int
    level_number: int
    start_date: date
    end_date: date


class LevelProgressionResult(BaseModel):
    """Output for level progression workflow."""
    old_level_number: int
    new_level_number: int
    new_level_id: int
    sessions_created: int
    enrollments_migrated: int
    message: str


class EnrollmentMigrationResult(BaseModel):
    """Output for enrollment migration."""
    count: int
    old_level: int
    new_level: int
    migrated_enrollment_ids: List[int]
    new_enrollment_ids: List[int]
    total_amount_due: float = 0.0


class GroupCreationResult(BaseModel):
    """Output for group + level + sessions creation."""
    group_id: int
    group_name: str
    level_id: int
    level_number: int
    sessions_count: int
    sessions: List[dict] #TODO remove Dict and write a typed DTO class
    message: str = "Group created successfully with Level 1 and sessions."
