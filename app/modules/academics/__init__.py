"""
app/modules/academics/__init__.py
──────────────────────────────────
Clean exports for the Academics module.

Import from this module or from specific submodules:
  - from app.modules.academics import CourseService, GroupService
  - from app.modules.academics.schemas import UpdateSessionDTO
"""
# ── Service Classes ─────────────────────────────────────────────────────────
from .services.course_service import CourseService
from .services.group_service import GroupCoreService
from .services.session_service import SessionService
from .services.group_lifecycle_service import GroupLifecycleService
from .services.group_details_service import GroupDetailsService
from .services.group_level_service import GroupLevelService
from .services.group_directory_service import GroupDirectoryService
from .services.group_analytics_service import GroupAnalyticsService

# ── Models ───────────────────────────────────────────────────────────────────
from .models.course_models import Course
from .models.group_models import Group
from .models.session_models import CourseSession
from .models.group_level_models import GroupLevel

# ── Schemas (DTOs) ───────────────────────────────────────────────────────────
from .schemas.course_schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from .schemas.group_schemas import ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO
from .schemas.session_schemas import AddExtraSessionInput, GenerateLevelSessionsInput, UpdateSessionDTO
from .schemas.group_lifecycle_schemas import (
    CreateGroupWithLevelDTO as CreateGroupDTO,
    CreateGroupLevelDTO,
    ProgressLevelDTO,
    GroupCreationResult,
    NextLevelCreationResult,
    SessionSummaryDTO,
)
from .schemas.group_details_schemas import (
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
    "GroupDirectoryService",
    "GroupAnalyticsService",
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
    "NextLevelCreationResult",
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
