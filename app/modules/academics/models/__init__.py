"""
app/modules/academics/models/__init__.py
────────────────────────────────────────
Exports all SQLModel entities for the academics module.
"""
from .course_models import Course, CourseBase
from .group_models import Group, GroupBase
from .session_models import CourseSession, CourseSessionBase
from .group_level_models import GroupLevel, GroupCourseHistory, GroupCompetitionParticipation


__all__ = [
    "Course",
    "CourseBase",
    "Group",
    "GroupBase",
    "CourseSession",
    "CourseSessionBase",
    "GroupLevel",
    "GroupCourseHistory",
    "GroupCompetitionParticipation",
]
