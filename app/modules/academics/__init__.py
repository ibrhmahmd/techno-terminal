"""
app/modules/academics/__init__.py
──────────────────────────────────
Clean exports for the Academics module.

Import from this module or from specific submodules:
  - from app.modules.academics import CourseService, GroupService
  - from app.modules.academics.schemas import UpdateSessionDTO
"""
# ── Service Classes ─────────────────────────────────────────────────────────
from .course.service import CourseService
from .group.core.service import GroupCoreService
from .session.service import SessionService
from .group.lifecycle.service import GroupLifecycleService
from .group.details.service import GroupDetailsService
from .group.level.service import GroupLevelService

# ── Models ───────────────────────────────────────────────────────────────────
from .models.course_models import Course
from .models.group_models import Group
from .models.session_models import CourseSession
from .models.group_level_models import GroupLevel

# ── Schemas (DTOs) ───────────────────────────────────────────────────────────
from .course.schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from .group.core.schemas import ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO
from .session.schemas import AddExtraSessionInput, GenerateLevelSessionsInput, UpdateSessionDTO
from .group.lifecycle.schemas import (
    CreateGroupWithLevelDTO as CreateGroupDTO,
    CreateGroupLevelDTO,
    ProgressLevelDTO,
    GroupCreationResult,
    LevelProgressionResult,
    SessionSummaryDTO,
)
from .group.details.schemas import (
    LevelDeleteResultDTO,
    CourseLookupDTO,
    InstructorLookupDTO,
    StudentLookupDTO,
    EnrollmentStatsDTO,
    PaymentStatsDTO,
)

# ── Constants ──────────────────────────────────────────────────────────────
from .constants import (
    GROUP_STATUS_ACTIVE,
    GROUP_STATUS_INACTIVE,
    GROUP_STATUS_COMPLETED,
    LEVEL_STATUS_ACTIVE,
    LEVEL_STATUS_COMPLETED,
    SESSION_STATUS_SCHEDULED,
    SESSION_STATUS_COMPLETED,
    SESSION_STATUS_CANCELLED,
    ENROLLMENT_STATUS_ACTIVE,
    ENROLLMENT_STATUS_COMPLETED,
    ENROLLMENT_STATUS_DROPPED,
)

__all__ = [
    # Services
    "CourseService",
    "GroupCoreService",
    "SessionService",
    "GroupLifecycleService",
    "GroupDetailsService",
    "GroupLevelService",
    # Models
    "Course",
    "Group",
    "CourseSession",
    "GroupLevel",
    # Input DTOs
    "AddNewCourseInput",
    "ScheduleGroupInput",
    "AddExtraSessionInput",
    "GenerateLevelSessionsInput",
    "CreateGroupDTO",
    "CreateGroupLevelDTO",
    "ProgressLevelDTO",
    # Update DTOs
    "UpdateCourseDTO",
    "UpdateGroupDTO",
    "UpdateSessionDTO",
    # Result DTOs
    "CourseStatsDTO",
    "EnrichedGroupDTO",
    "GroupCreationResult",
    "LevelProgressionResult",
    "SessionSummaryDTO",
    # Group Details DTOs
    "LevelDeleteResultDTO",
    "CourseLookupDTO",
    "InstructorLookupDTO",
    "StudentLookupDTO",
    "EnrollmentStatsDTO",
    "PaymentStatsDTO",
    # Constants
    "GROUP_STATUS_ACTIVE",
    "GROUP_STATUS_INACTIVE",
    "GROUP_STATUS_COMPLETED",
    "LEVEL_STATUS_ACTIVE",
    "LEVEL_STATUS_COMPLETED",
    "SESSION_STATUS_SCHEDULED",
    "SESSION_STATUS_COMPLETED",
    "SESSION_STATUS_CANCELLED",
    "ENROLLMENT_STATUS_ACTIVE",
    "ENROLLMENT_STATUS_COMPLETED",
    "ENROLLMENT_STATUS_DROPPED",
]
