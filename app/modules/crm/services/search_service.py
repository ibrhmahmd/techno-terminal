"""
SearchService - Handles student search, listing, and counting operations.
Delegates to SearchRepository for raw SQL queries.
"""
from typing import List, Literal

from app.db.uow import UnitOfWork
from app.modules.crm.repositories import SearchRepository
from app.modules.crm.schemas import (
    StudentSummaryDTO,
    StudentGroupedResultDTO,
    StudentFilterDTO,
    StudentFilterResultDTO,
)
from app.modules.crm.schemas.student_schemas import StudentStatusSummaryDTO
from app.modules.crm.schemas.waiting_list import WaitingListStudentDTO


class SearchService:
    """Service for student search and listing operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._search_repo = SearchRepository(uow.session)

    def search(self, query: str, skip: int = 0, limit: int = 50) -> List[StudentSummaryDTO]:
        """One page of students matching ``query`` by name or phone."""
        return self._search_repo.search(query, skip, limit)

    def count_search(self, query: str) -> int:
        """How many students match ``query`` by name or phone."""
        return self._search_repo.count_search(query)

    def list_all(self, skip: int = 0, limit: int = 200) -> List[StudentSummaryDTO]:
        """List all students with pagination."""
        return self._search_repo.list_all(skip, limit)

    def count(self, active_only: bool = True) -> int:
        """Count total students."""
        return self._search_repo.count(active_only)

    def get_by_status(self, status) -> List:
        """Get all students with a specific status."""
        return self._search_repo.get_by_status(status)

    def get_waiting_list(self) -> List[WaitingListStudentDTO]:
        """Get all students on the waiting list with unpaid balance and age."""
        return self._search_repo.get_waiting_list()

    def get_status_summary(self) -> StudentStatusSummaryDTO:
        """Get summary counts by status."""
        return self._search_repo.get_status_summary()

    def get_grouped(
        self,
        group_by: Literal["status", "gender", "age_bucket"],
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> StudentGroupedResultDTO:
        """
        Group students by specified criteria.

        Args:
            group_by: Grouping strategy - "status", "gender", or "age_bucket"
            include_inactive: Whether to include inactive students
            skip: Number of students to skip per group (pagination)
            limit: Max students per group (pagination)
        """
        return self._search_repo.get_grouped(group_by, include_inactive, skip, limit)

    def filter_students(self, filters: StudentFilterDTO) -> StudentFilterResultDTO:
        """
        Filter students based on multiple criteria using optimized raw SQL with CTEs.
        """
        return self._search_repo.filter_students(filters)