"""
app/modules/academics/repositories/__init__.py
───────────────────────────────────────────────
Facade for exporting all repository layer functions for the academics module.
Maintains backward compatibility for academics_service.py during migration.
"""

from .course_repository import (
    create_course,
    get_course_by_name,
    list_active_courses,
    update_course_price,
    get_course_by_id,
    # Protocol aliases
    get_by_id,
    create,
    list_all,
)

from .group_repository import (
    create_group,
    list_groups_by_course,
    list_all_active_groups,
    get_group_by_id,
    increment_group_level,
    get_enriched_groups,
    get_enriched_groups_by_date,
    get_enriched_group_by_id,
    search_groups,
    get_groups_by_type,
    get_groups_by_course,
    delete_group_by_id,
)



from .group_competition_repository import (
    create_participation,
    get_participation_by_id,
    list_group_participations,
    list_team_participations,
    complete_participation,
    update_participation,
    get_active_participation_for_team,
)



from .group_level_repository import (
    list_group_levels,
    get_current_group_level,
    get_group_level_by_id,
    get_group_level_by_number,
    update_group_level,
    complete_group_level,
    cancel_group_level
)

from .session_repository import (
    create_session,
    delete_session,
    list_sessions,
    get_session_by_id,
    count_sessions,
    get_max_session_number,
    update_session_instructor,
)

from .course_stats_repository import (
    get_all_course_stats,
    get_course_stats,
)

from .group_history_repository import (
    get_group_levels_with_details,
    get_level_student_counts,
    get_group_enrollments_with_details,
    get_group_enrollment_stats,
    get_enrollment_payments,
    get_group_instructors_summary,
    get_group_competition_participations,
)

__all__ = [
    # Course Repository
    "create_course",
    "get_course_by_name",
    "list_active_courses",
    "update_course_price",
    "get_course_by_id",
    "get_by_id",
    "create",
    "list_all",
    
    # Group Repository
    "create_group",
    "list_groups_by_course",
    "list_all_active_groups",
    "get_group_by_id",
    "increment_group_level",
    "get_enriched_groups",
    "get_enriched_groups_by_date",
    "get_enriched_group_by_id",
    "search_groups",
    "get_groups_by_type",
    "get_groups_by_course",
    "delete_group_by_id",
    
    # Group Levels Repository
    "list_group_levels",
    "get_current_group_level",
    "get_group_level_by_id",
    "get_group_level_by_number",
    "update_group_level",
    "complete_group_level",
    "cancel_group_level",
    


    # group competition repository
    "create_participation",
    "get_participation_by_id",
    "list_group_participations",
    "list_team_participations",
    "complete_participation",
    "update_participation",
    "get_active_participation_for_team",
    
    # Session Repository
    "create_session",
    "delete_session",
    "list_sessions",
    "get_session_by_id",
    "count_sessions",
    "get_max_session_number",
    "update_session_instructor",
    
    # Course Stats Repository
    "get_all_course_stats",
    "get_course_stats",
    
    # Group History Repository (Analytics)
    "get_group_levels_with_details",
    "get_level_student_counts",
    "get_group_enrollments_with_details",
    "get_group_enrollment_stats",
    "get_enrollment_payments",
    "get_group_instructors_summary",
    "get_group_competition_participations",
]

