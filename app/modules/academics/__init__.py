from .academics_service import (
    add_new_course,
    update_course_price,
    update_course,
    get_active_courses,
    get_all_course_stats,
    get_course_stats,
    schedule_group,
    get_groups_by_course,
    get_all_active_groups,
    get_all_active_groups_enriched,
    get_todays_groups_enriched,
    get_group_by_id,
    update_group,
    generate_level_sessions,
    add_extra_session,
    update_session,
    delete_session,
    mark_substitute_instructor,
    list_group_sessions,
    check_level_complete,
    advance_group_level,
)
from .academics_models import Course, Group
from .academics_session_models import CourseSession
from .schemas import (
    AddNewCourseInput,
    ScheduleGroupInput,
    AddExtraSessionInput,
    GenerateLevelSessionsInput,
    UpdateCourseDTO,
    UpdateGroupDTO,
    UpdateSessionDTO,
    CourseStatsDTO,
    EnrichedGroupDTO,
)

__all__ = [
    # Course service
    "add_new_course",
    "update_course_price",
    "update_course",
    "get_active_courses",
    "get_all_course_stats",
    "get_course_stats",
    # Group service
    "schedule_group",
    "get_groups_by_course",
    "get_all_active_groups",
    "get_all_active_groups_enriched",
    "get_todays_groups_enriched",
    "get_group_by_id",
    "update_group",
    # Session service
    "generate_level_sessions",
    "add_extra_session",
    "update_session",
    "delete_session",
    "mark_substitute_instructor",
    "list_group_sessions",
    "check_level_complete",
    "advance_group_level",
    # Models
    "Course",
    "Group",
    "CourseSession",
    # Input DTOs
    "AddNewCourseInput",
    "ScheduleGroupInput",
    "AddExtraSessionInput",
    "GenerateLevelSessionsInput",
    # Update DTOs
    "UpdateCourseDTO",
    "UpdateGroupDTO",
    "UpdateSessionDTO",
    # Read DTOs
    "CourseStatsDTO",
    "EnrichedGroupDTO",
]
