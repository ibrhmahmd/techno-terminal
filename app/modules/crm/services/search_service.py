"""
SearchService - Handles student search, listing, and counting operations.
Implements ISearchService protocol.
"""
from typing import List, Literal
from collections import defaultdict

from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.interfaces.dtos import (
    StudentSummaryDTO,
    StudentStatusSummaryDTO,
    StudentGroupedResultDTO,
    StudentGroupBucketDTO,
)
from app.modules.crm.validators.student_validator import StudentValidator


class SearchService:
    """Service for student search and listing operations."""
    
    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow
    
    def search(self, query: str) -> List[Student]:
        """Search students by name or phone."""
        if not query or len(query.strip()) < 2:
            return []
        return list(self._uow.students.search(query.strip()))
    
    def list_all(self, skip: int = 0, limit: int = 200) -> List[Student]:
        """List all students with pagination."""
        return list(self._uow.students.get_all(skip, limit))
    
    def list_all_enriched(self, include_inactive: bool = False) -> List[StudentSummaryDTO]:
        """List all students with enriched summary data."""
        return list(self._uow.students.get_all_enriched(include_inactive))
    
    def count(self, active_only: bool = True) -> int:
        """Count total students."""
        return self._uow.students.count(active_only)
    
    def count_by_status(self, status: StudentStatus) -> int:
        """Count students by specific status."""
        return self._uow.students.count_by_status(status)
    
    def get_by_status(self, status: StudentStatus) -> List[Student]:
        """Get all students with a specific status."""
        return list(self._uow.students.get_by_status(status))
    
    def get_waiting_list(self) -> List[Student]:
        """Get all students on the waiting list, ordered by priority."""
        return list(self._uow.students.get_waiting_list())
    
    def get_status_summary(self) -> StudentStatusSummaryDTO:
        """Get summary counts by status."""
        total_active = self.count(active_only=True)
        total_inactive = self.count(active_only=False) - total_active
        
        return StudentStatusSummaryDTO(
            total=total_active + total_inactive,
            active=total_active,
            inactive=total_inactive,
            waiting=self.count_by_status(StudentStatus.WAITING),
        )
    
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
        # Get all enriched student data
        students = self._uow.students.get_all_enriched(include_inactive)

        # Group by strategy
        buckets: dict[str, list[StudentSummaryDTO]] = defaultdict(list)

        for student in students:
            if group_by == "status":
                key = student.status
            elif group_by == "gender":
                key = student.gender or "unknown"
            elif group_by == "age_bucket":
                age = StudentValidator.compute_age(student.date_of_birth)
                key = StudentValidator.classify_age_bracket(age)
            else:
                key = "other"

            buckets[key].append(student)

        # Build result buckets with pagination applied to each group
        groups = []
        for key, students_list in sorted(buckets.items()):
            total_in_group = len(students_list)
            # Apply pagination: slice [skip:skip+limit]
            paginated_students = students_list[skip:skip + limit]
            groups.append(
                StudentGroupBucketDTO(
                    key=key,
                    label=key.replace("_", " ").title() if group_by != "status" else key.capitalize(),
                    count=total_in_group,  # Total count (unpaginated)
                    students=paginated_students,  # Paginated list
                )
            )

        return StudentGroupedResultDTO(
            group_by=group_by,
            total_unique_students=len(students),
            groups=groups,
            total=sum(len(g.students) for g in groups),
        )
