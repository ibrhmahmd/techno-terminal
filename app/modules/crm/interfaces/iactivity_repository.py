"""
app/modules/crm/interfaces/iactivity_repository.py
────────────────────────────────────────────────
Protocol for activity repository operations.
"""
from typing import Protocol, Optional, List, Dict, Any, Tuple
from datetime import datetime

from app.modules.crm.models.activity_models import StudentActivityLog
from app.modules.crm.interfaces.dtos import (
    EnrollmentHistoryDTO,
    StatusHistoryDTO,
    CompetitionHistoryDTO,
)


class IActivityRepository(Protocol):
    """Protocol for student activity repository operations."""

    def create_activity_log(
        self,
        student_id: int,
        activity_type: str,
        activity_subtype: Optional[str],
        reference_type: Optional[str],
        reference_id: Optional[int],
        description: str,
        metadata: Dict[str, Any],
        performed_by: Optional[int],
    ) -> StudentActivityLog: ...

    def get_student_activity_timeline(
        self,
        student_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int = 100,
    ) -> List[StudentActivityLog]: ...

    def get_enrollment_history_by_student(
        self, student_id: int, limit: int, offset: int
    ) -> Tuple[List[EnrollmentHistoryDTO], int]: ...

    def get_status_history_by_student(
        self, student_id: int, limit: int, offset: int
    ) -> Tuple[List[StatusHistoryDTO], int]: ...

    def get_competition_history_by_student(
        self, student_id: int, limit: int, offset: int
    ) -> Tuple[List[CompetitionHistoryDTO], int]: ...

    def get_payment_activities(self, student_id: int, limit: int = 50) -> List[StudentActivityLog]: ...

    def get_recent_activities(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> List[StudentActivityLog]: ...

    def get_activity_summary(self, student_id: int) -> Dict[str, Any]: ... #TODO remove Dict and write a typed DTO class
