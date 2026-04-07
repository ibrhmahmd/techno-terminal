from .services import CourseService, GroupService, SessionService

# ── Compatibility Facades ─────────────────────────────────────────────────────
# These module-level exports maintain backward compatibility with existing
# call sites (e.g., UI components) while the internal implementation uses
# the new class-based services.
# Once all call sites are migrated to use the classes directly (Phase 6),
# these facades can be removed.

_course_svc = CourseService()
_group_svc = GroupService()
_session_svc = SessionService()

# Course service
add_new_course = _course_svc.add_new_course
update_course_price = _course_svc.update_course_price
update_course = _course_svc.update_course
get_active_courses = _course_svc.get_active_courses
get_all_course_stats = _course_svc.get_all_course_stats
get_course_stats = _course_svc.get_course_stats

# Group service
schedule_group = _group_svc.schedule_group
get_groups_by_course = _group_svc.get_groups_by_course
get_all_active_groups = _group_svc.get_all_active_groups
get_all_active_groups_enriched = _group_svc.get_all_active_groups_enriched
get_todays_groups_enriched = _group_svc.get_todays_groups_enriched
get_group_by_id = _group_svc.get_group_by_id
update_group = _group_svc.update_group
delete_group_by_id = _group_svc.delete_group_by_id

# Session service
generate_level_sessions = _session_svc.generate_level_sessions
add_extra_session = _session_svc.add_extra_session
update_session = _session_svc.update_session
delete_session = _session_svc.delete_session
mark_substitute_instructor = _session_svc.mark_substitute_instructor
list_group_sessions = _session_svc.list_group_sessions
check_level_complete = _session_svc.check_level_complete
progress_group_level = _session_svc.progress_group_level
cancel_session = _session_svc.cancel_session

from .models import Course, Group
from .models import CourseSession
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
    "delete_group_by_id",
    # Session service
    "generate_level_sessions",
    "add_extra_session",
    "update_session",
    "delete_session",
    "mark_substitute_instructor",
    "list_group_sessions",
    "check_level_complete",
    "progress_group_level",
    "cancel_session",
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
