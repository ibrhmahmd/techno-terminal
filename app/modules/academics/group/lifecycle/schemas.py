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

from app.modules.academics.constants import DEFAULT_SESSIONS_PER_LEVEL
from app.modules.academics.constants import LEVEL_STATUS_ACTIVE
from app.modules.academics.group.core.schemas import ScheduleGroupInput


# ═══════════════════════════════════════════════════════════════════════════════
# Input DTOs
# ═══════════════════════════════════════════════════════════════════════════════


class CreateGroupLevelDTO(BaseModel):
    """Input for creating a group level."""
    group_id: int
    level_number: int
    course_id: int
    instructor_id: Optional[int] = None
    sessions_planned: int = Field(default=DEFAULT_SESSIONS_PER_LEVEL)
    price_override: Optional[Decimal] = None
    start_date: Optional[date] = None
    status: str = LEVEL_STATUS_ACTIVE




class ProgressLevelDTO(BaseModel):
    """Input for progressing to next level."""
    group_id: int
    price_override: Optional[Decimal] = None
    auto_migrate_enrollments: bool = True
    target_level: Optional[int] = None
    complete_current_level: bool = True
    instructor_id: Optional[int] = None
    session_start_date: Optional[date] = None
    course_id: Optional[int] = None
    group_name: Optional[str] = None


class CreateGroupWithLevelDTO(BaseModel):
    """Input for creating group with first level."""
    group_input: ScheduleGroupInput
    sessions_per_level: int = DEFAULT_SESSIONS_PER_LEVEL
    start_date: Optional[date] = None




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


class SessionSummaryDTO(BaseModel):
    """Summary of a session for result DTOs."""
    id: int
    session_number: int
    session_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str


class SessionGenerationResult(BaseModel):
    """Output for session generation."""
    sessions: List[SessionSummaryDTO]
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


class GroupCreationResult(BaseModel):
    """Output for group + level + sessions creation."""
    group_id: int
    group_name: str
    level_id: int
    level_number: int
    sessions_count: int
    sessions: List[SessionSummaryDTO]
    message: str = "Group created successfully with Level 1 and sessions."


class DeleteLevelResult(BaseModel):
    """Result of undoing/deleting a level."""
    level_number_deleted: int
    reverted_to_level: int
    sessions_deleted: int
    enrollments_deleted: int
    enrollments_reactivated: int
    payments_voided: int
    group_level_number_after: int
