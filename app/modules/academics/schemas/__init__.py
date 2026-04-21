"""
app/modules/academics/schemas/__init__.py
──────────────────────────────────────────
Re-exports all schema DTOs for backward compatibility.
Import from this module or from individual entity schema files.
"""
from .course_schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from .group_schemas import (
    ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO, WeekDay,
    ProgressGroupLevelInput, ProgressGroupLevelResult,
)
from .session_schemas import AddExtraSessionInput, GenerateLevelSessionsInput, UpdateSessionDTO

__all__ = [
    # Course
    "AddNewCourseInput",
    "UpdateCourseDTO",
    "CourseStatsDTO",
    # Group
    "ScheduleGroupInput",
    "UpdateGroupDTO",
    "EnrichedGroupDTO",
    "WeekDay",
    # Group Level Management
    "ProgressGroupLevelInput",
    "ProgressGroupLevelResult",
    # Session
    "AddExtraSessionInput",
    "GenerateLevelSessionsInput",
    "UpdateSessionDTO",
]
