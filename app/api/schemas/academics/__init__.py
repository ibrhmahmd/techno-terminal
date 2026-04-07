"""
app/api/schemas/academics/__init__.py
"""
from .course import CoursePublic
from .group import GroupPublic, GroupListItem
from .session import SessionPublic
from .group_analytics import (
    GroupLevelHistoryItemDTO,
    GroupLevelHistoryResponseDTO,
    EnrollmentHistoryItemDTO,
    GroupEnrollmentHistoryResponseDTO,
    CompetitionHistoryItemDTO,
    GroupCompetitionHistoryResponseDTO,
    InstructorHistoryItemDTO,
    GroupInstructorHistoryResponseDTO,
)

__all__ = [
    "CoursePublic",
    "GroupPublic",
    "GroupListItem",
    "SessionPublic",
    # Group Analytics
    "GroupLevelHistoryItemDTO",
    "GroupLevelHistoryResponseDTO",
    "EnrollmentHistoryItemDTO",
    "GroupEnrollmentHistoryResponseDTO",
    "CompetitionHistoryItemDTO",
    "GroupCompetitionHistoryResponseDTO",
    "InstructorHistoryItemDTO",
    "GroupInstructorHistoryResponseDTO",
]
