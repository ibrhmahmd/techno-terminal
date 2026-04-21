"""
app/modules/crm/repositories/activity_repository.py
─────────────────────────────────────────────────
Repository for student activity logging operations.
Uses raw SQL for all queries (no ORM model instantiation).
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlmodel import Session
from sqlalchemy import text

from app.modules.crm.interfaces.iactivity_repository import IActivityRepository
from app.modules.crm.models.activity_models import StudentActivityLog
from app.modules.crm.interfaces.dtos import (
    EnrollmentHistoryDTO,
    StatusHistoryDTO,
    CompetitionHistoryDTO,
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
        sql = """
            SELECT id, student_id, activity_type, activity_subtype,
                   reference_type, reference_id, description, meta,
                   performed_by, created_at
            FROM student_activity_log
            WHERE student_id = :student_id
        """
        params: Dict[str, Any] = {"student_id": student_id}

        if start_date:
            sql += " AND created_at >= :start_date"
            params["start_date"] = start_date
        if end_date:
            sql += " AND created_at <= :end_date"
            params["end_date"] = end_date

        sql += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit

        result = self._session.exec(text(sql), params=params)
        return [
            StudentActivityLog(
                id=row.id,
                student_id=row.student_id,
                activity_type=row.activity_type,
                activity_subtype=row.activity_subtype,
                reference_type=row.reference_type,
                reference_id=row.reference_id,
                description=row.description,
                meta=row.meta,
                performed_by=row.performed_by,
                created_at=row.created_at,
            )
            for row in result
        ]

    def get_enrollment_history_by_student(
        self,
        student_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EnrollmentHistoryDTO], int]:
        """Get enrollment lifecycle events from activity_log using raw SQL."""
        sql = """
            SELECT 
                al.id,
                al.student_id,
                (al.meta->>'enrollment_id')::int as enrollment_id,
                (al.meta->>'group_id')::int as group_id,
                al.meta->>'group_name' as group_name,
                (al.meta->>'level_number')::int as level_number,
                al.meta->>'enrollment_status' as enrollment_status,
                (al.meta->>'amount_due')::decimal as amount_due,
                (al.meta->>'discount_applied')::decimal as discount_applied,
                COALESCE(al.meta->>'action', al.activity_subtype) as action,
                al.created_at as action_date,
                (al.meta->>'old_group_id')::int as previous_group_id,
                (al.meta->>'old_level_number')::int as previous_level_number,
                al.meta->>'old_status' as previous_status,
                al.meta->>'transfer_reason' as transfer_reason,
                al.performed_by,
                u.username as performed_by_name,
                al.description as notes
            FROM student_activity_log al
            LEFT JOIN users u ON u.id = al.performed_by
            WHERE al.student_id = :student_id
              AND al.activity_type IN ('enrollment', 'enrollment_change')
            ORDER BY al.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        result = self._session.exec(text(sql), params={
            "student_id": student_id,
            "limit": limit,
            "offset": offset
        })

        dtos = [
            EnrollmentHistoryDTO(
                id=row.id,
                student_id=row.student_id,
                enrollment_id=row.enrollment_id,
                group_id=row.group_id,
                group_name=row.group_name,
                level_number=row.level_number,
                enrollment_status=row.enrollment_status,
                amount_due=row.amount_due,
                discount_applied=row.discount_applied,
                action=row.action,
                action_date=row.action_date,
                previous_group_id=row.previous_group_id,
                previous_level_number=row.previous_level_number,
                previous_status=row.previous_status,
                transfer_reason=row.transfer_reason,
                performed_by=row.performed_by,
                performed_by_name=row.performed_by_name,
                notes=row.notes,
            )
            for row in result
        ]

        count_sql = """
            SELECT COUNT(*) 
            FROM student_activity_log 
            WHERE student_id = :student_id
              AND activity_type IN ('enrollment', 'enrollment_change')
        """
        count_result = self._session.exec(text(count_sql), params={"student_id": student_id})
        total = count_result.scalar() or 0

        return dtos, total

    def get_status_history_by_student(
        self,
        student_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[StatusHistoryDTO], int]:
        """Get status change events from activity_log using raw SQL."""
        sql = """
            SELECT 
                al.id,
                al.student_id,
                al.meta->>'old_status' as old_status,
                COALESCE(al.meta->>'new_status', al.activity_subtype) as new_status,
                al.created_at as changed_at,
                al.performed_by as changed_by,
                u.username as changed_by_name,
                al.meta->>'reason' as reason,
                al.description as notes
            FROM student_activity_log al
            LEFT JOIN users u ON u.id = al.performed_by
            WHERE al.student_id = :student_id
              AND al.activity_type = 'status_change'
            ORDER BY al.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        result = self._session.exec(text(sql), params={
            "student_id": student_id,
            "limit": limit,
            "offset": offset
        })

        dtos = [
            StatusHistoryDTO(
                id=row.id,
                student_id=row.student_id,
                old_status=row.old_status,
                new_status=row.new_status,
                changed_at=row.changed_at,
                changed_by=row.changed_by,
                changed_by_name=row.changed_by_name,
                reason=row.reason,
                notes=row.notes,
            )
            for row in result
        ]

        count_sql = """
            SELECT COUNT(*) 
            FROM student_activity_log 
            WHERE student_id = :student_id 
              AND activity_type = 'status_change'
        """
        count_result = self._session.exec(text(count_sql), params={"student_id": student_id})
        total = count_result.scalar() or 0

        return dtos, total

    def get_competition_history_by_student(
        self,
        student_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CompetitionHistoryDTO], int]:
        """Get competition events from activity_log using raw SQL."""
        sql = """
            SELECT 
                al.id,
                al.student_id,
                (al.meta->>'competition_id')::int as competition_id,
                al.meta->>'competition_name' as competition_name,
                (al.meta->>'team_id')::int as team_id,
                al.meta->>'team_name' as team_name,
                COALESCE(al.meta->>'participation_type', al.activity_subtype) as participation_type,
                (al.meta->>'registration_date')::timestamp as registration_date,
                (al.meta->>'subscription_amount')::decimal as subscription_amount,
                (al.meta->>'subscription_paid')::boolean as subscription_paid,
                (al.meta->>'payment_id')::int as payment_id,
                (al.meta->>'result_position')::int as result_position,
                al.meta->>'result_notes' as result_notes,
                al.performed_by,
                u.username as performed_by_name,
                al.created_at
            FROM student_activity_log al
            LEFT JOIN users u ON u.id = al.performed_by
            WHERE al.student_id = :student_id
              AND al.activity_type = 'competition'
            ORDER BY al.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        result = self._session.exec(text(sql), params={
            "student_id": student_id,
            "limit": limit,
            "offset": offset
        })

        dtos = [
            CompetitionHistoryDTO(
                id=row.id,
                student_id=row.student_id,
                competition_id=row.competition_id,
                competition_name=row.competition_name,
                team_id=row.team_id,
                team_name=row.team_name,
                participation_type=row.participation_type,
                registration_date=row.registration_date,
                subscription_amount=row.subscription_amount,
                subscription_paid=row.subscription_paid,
                payment_id=row.payment_id,
                result_position=row.result_position,
                result_notes=row.result_notes,
                performed_by=row.performed_by,
                performed_by_name=row.performed_by_name,
                created_at=row.created_at,
            )
            for row in result
        ]

        count_sql = """
            SELECT COUNT(*) 
            FROM student_activity_log 
            WHERE student_id = :student_id 
              AND activity_type = 'competition'
        """
        count_result = self._session.exec(text(count_sql), params={"student_id": student_id})
        total = count_result.scalar() or 0

        return dtos, total

    def get_payment_activities(
        self, student_id: int, limit: int = 50
    ) -> List[StudentActivityLog]:
        """Get payment-related activity entries for a student using raw SQL."""
        sql = """
            SELECT id, student_id, activity_type, activity_subtype,
                   reference_type, reference_id, description, meta,
                   performed_by, created_at
            FROM student_activity_log
            WHERE student_id = :student_id
              AND activity_type = 'payment'
            ORDER BY created_at DESC
            LIMIT :limit
        """
        result = self._session.exec(text(sql), params={
            "student_id": student_id,
            "limit": limit
        })
        return [
            StudentActivityLog(
                id=row.id,
                student_id=row.student_id,
                activity_type=row.activity_type,
                activity_subtype=row.activity_subtype,
                reference_type=row.reference_type,
                reference_id=row.reference_id,
                description=row.description,
                meta=row.meta,
                performed_by=row.performed_by,
                created_at=row.created_at,
            )
            for row in result
        ]

    def get_recent_activities(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> List[StudentActivityLog]:
        """Get recent activities across all students using raw SQL."""
        since = datetime.utcnow() - timedelta(days=days)
        sql = """
            SELECT id, student_id, activity_type, activity_subtype,
                   reference_type, reference_id, description, meta,
                   performed_by, created_at
            FROM student_activity_log
            WHERE created_at >= :since
            ORDER BY created_at DESC
            LIMIT :limit
        """
        result = self._session.exec(text(sql), params={"since": since, "limit": limit})
        return [
            StudentActivityLog(
                id=row.id,
                student_id=row.student_id,
                activity_type=row.activity_type,
                activity_subtype=row.activity_subtype,
                reference_type=row.reference_type,
                reference_id=row.reference_id,
                description=row.description,
                meta=row.meta,
                performed_by=row.performed_by,
                created_at=row.created_at,
            )
            for row in result
        ]

    def get_activity_summary(self, student_id: int) -> Dict[str, Any]:
        """Get activity summary statistics for a student using raw SQL."""
        # Total count
        count_sql = """
            SELECT COUNT(*) 
            FROM student_activity_log 
            WHERE student_id = :student_id
        """
        count_result = self._session.exec(text(count_sql), params={"student_id": student_id})
        total = count_result.scalar() or 0

        # Count by type
        type_sql = """
            SELECT activity_type, COUNT(*)
            FROM student_activity_log
            WHERE student_id = :student_id
            GROUP BY activity_type
        """
        type_result = self._session.exec(text(type_sql), params={"student_id": student_id})
        by_type = {row[0]: row[1] for row in type_result}

        # Date range
        range_sql = """
            SELECT MIN(created_at), MAX(created_at)
            FROM student_activity_log
            WHERE student_id = :student_id
        """
        range_result = self._session.exec(text(range_sql), params={"student_id": student_id})
        row = range_result.first()
        first_activity = row[0] if row else None
        last_activity = row[1] if row else None

        return {
            "total_activities": total,
            "activities_by_type": by_type,
            "first_activity_date": first_activity,
            "last_activity_date": last_activity,
        }
