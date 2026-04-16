"""
app/modules/crm/repositories/activity_repository.py
─────────────────────────────────────────────────
Repository for student activity logging operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlmodel import Session, select, func
from sqlalchemy import desc

from app.modules.crm.interfaces.iactivity_repository import IActivityRepository
from app.modules.crm.models.activity_models import (
    StudentActivityLog,
    StudentEnrollmentHistory,
    StudentCompetitionHistory,
)


class ActivityRepository(IActivityRepository):
    """Repository for student activity logging and history tracking."""

    def __init__(self, session: Session) -> None:
        self._session = session

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
    ) -> StudentActivityLog:
        """Create a new activity log entry."""
        log = StudentActivityLog(
            student_id=student_id,
            activity_type=activity_type,
            activity_subtype=activity_subtype,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            meta=metadata,
            performed_by=performed_by,
            created_at=datetime.utcnow(),
        )
        self._session.add(log)
        self._session.flush()
        return log

    def get_student_activity_timeline(
        self,
        student_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[StudentActivityLog]:
        """Get activity timeline for a student with optional date filtering."""
        stmt = (
            select(StudentActivityLog)
            .where(StudentActivityLog.student_id == student_id)
            .order_by(desc(StudentActivityLog.created_at))
            .limit(limit)
        )

        if start_date:
            stmt = stmt.where(StudentActivityLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(StudentActivityLog.created_at <= end_date)

        return list(self._session.exec(stmt).all())

    def get_enrollment_changes(self, student_id: int) -> List[StudentEnrollmentHistory]:
        """Get all enrollment lifecycle events for a student."""
        stmt = (
            select(StudentEnrollmentHistory)
            .where(StudentEnrollmentHistory.student_id == student_id)
            .order_by(desc(StudentEnrollmentHistory.action_date))
        )
        return list(self._session.exec(stmt).all())

    def get_competition_participations(self, student_id: int) -> List[StudentCompetitionHistory]:
        """Get all competition participation records for a student."""
        stmt = (
            select(StudentCompetitionHistory)
            .where(StudentCompetitionHistory.student_id == student_id)
            .order_by(desc(StudentCompetitionHistory.registration_date))
        )
        return list(self._session.exec(stmt).all())

    def get_payment_activities(
        self, student_id: int, limit: int = 50
    ) -> List[StudentActivityLog]:
        """Get payment-related activity entries for a student."""
        stmt = (
            select(StudentActivityLog)
            .where(StudentActivityLog.student_id == student_id)
            .where(StudentActivityLog.activity_type == "payment")
            .order_by(desc(StudentActivityLog.created_at))
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_recent_activities(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> List[StudentActivityLog]:
        """Get recent activities across all students."""
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(StudentActivityLog)
            .where(StudentActivityLog.created_at >= since)
            .order_by(desc(StudentActivityLog.created_at))
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_activity_summary(self, student_id: int) -> Dict[str, Any]:
        """Get activity summary statistics for a student."""
        # Total count
        count_stmt = select(func.count()).where(
            StudentActivityLog.student_id == student_id
        )
        total = self._session.exec(count_stmt).one()

        # Count by type
        type_stmt = (
            select(StudentActivityLog.activity_type, func.count())
            .where(StudentActivityLog.student_id == student_id)
            .group_by(StudentActivityLog.activity_type)
        )
        by_type = {row[0]: row[1] for row in self._session.exec(type_stmt).all()}

        # Date range
        range_stmt = (
            select(
                func.min(StudentActivityLog.created_at),
                func.max(StudentActivityLog.created_at),
            )
            .where(StudentActivityLog.student_id == student_id)
        )
        result = self._session.exec(range_stmt).first()
        first_activity = result[0] if result else None
        last_activity = result[1] if result else None

        return {
            "total_activities": total,
            "activities_by_type": by_type,
            "first_activity_date": first_activity,
            "last_activity_date": last_activity,
        }
