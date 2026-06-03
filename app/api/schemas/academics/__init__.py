"""
app/api/schemas/academics/__init__.py
"""
from .course import CoursePublic
from .group import GroupPublic
from .session import SessionPublic

__all__ = [
    "CoursePublic",
    "GroupPublic",
    "SessionPublic",
]
