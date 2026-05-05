"""
app/modules/academics/group/analytics/interface.py
────────────────────────────────────────
Interfaces for the Group Analytics slice.
"""
from typing import Protocol, runtime_checkable
from app.modules.academics.group.analytics.schemas import (
    GroupEnrollmentHistoryResponseDTO,
    GroupCompetitionHistoryResponseDTO,
    GroupInstructorHistoryResponseDTO,
)


@runtime_checkable
class GroupAnalyticsServiceInterface(Protocol):
    """Contract for Group Analytics business logic."""
    def get_enrollment_history(self, group_id: int, status: str | None = None, skip: int = 0, limit: int = 100) -> GroupEnrollmentHistoryResponseDTO: ...
    def get_competition_history(self, group_id: int) -> GroupCompetitionHistoryResponseDTO: ...
    def get_instructor_history(self, group_id: int) -> GroupInstructorHistoryResponseDTO: ...
