"""
app/modules/academics/services/__init__.py
───────────────────────────────────────────
Exports all service classes for the academics module.
"""
from .course_service import CourseService
from .group_service import GroupService
from .session_service import SessionService

__all__ = [
    "CourseService",
    "GroupService",
    "SessionService",
]
