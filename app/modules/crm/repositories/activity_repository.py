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
    ActivitySummaryDTO,
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
        created_at: Optional[datetime] = None,
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
            created_at=created_at or datetime.utcnow(),
        )
        self._session.add(log)
        self._session.flush()
        return log

    def get_activity_log_by_id(self, activity_id: int) -> Optional[StudentActivityLog]:
        """Retrieve a single activity log entry by ID."""
        sql = """
            SELECT id, student_id, activity_type, activity_subtype,
                   reference_type, reference_id, description, meta,
                   performed_by, created_at
            FROM student_activity_log
            WHERE id = :activity_id
        """
        result = self._session.exec(text(sql), params={"activity_id": activity_id}).first()
        if not result:
            return None
        return StudentActivityLog(
            id=result.id,
            student_id=result.student_id,
            activity_type=result.activity_type,
            activity_subtype=result.activity_subtype,
            reference_type=result.reference_type,
            reference_id=result.reference_id,
            description=result.description,
            meta=result.meta,
            performed_by=result.performed_by,
            created_at=result.created_at,
        )

    def update_activity_log(
        self,
        activity_id: int,
        activity_type: Optional[str] = None,
        activity_subtype: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> StudentActivityLog:
        """Update fields of an activity log entry."""
        # Retrieve the existing ORM entity so we can update it
        log = self._session.get(StudentActivityLog, activity_id)
        if not log:
            raise ValueError(f"Activity log with ID {activity_id} not found")

        if activity_type is not None:
            log.activity_type = activity_type
        if activity_subtype is not None:
            log.activity_subtype = activity_subtype
        if reference_type is not None:
            log.reference_type = reference_type
        if reference_id is not None:
            log.reference_id = reference_id
        if description is not None:
            log.description = description
        if metadata is not None:
            log.meta = metadata
        if created_at is not None:
            log.created_at = created_at

        self._session.add(log)
        self._session.flush()
        return log

    def delete_activity_log(self, activity_id: int) -> None:
        """Delete an activity log entry by ID."""
        log = self._session.get(StudentActivityLog, activity_id)
        if log:
            self._session.delete(log)
            self._session.flush()

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
                COALESCE((al.meta->>'competition_id')::int, 0) as competition_id,
                al.meta->>'competition_name' as competition_name,
                (al.meta->>'team_id')::int as team_id,
                al.meta->>'team_name' as team_name,
                COALESCE(al.meta->>'participation_type', al.activity_subtype) as participation_type,
                (al.meta->>'registration_date')::timestamp as registration_date,
                COALESCE((al.meta->>'subscription_amount')::decimal, (al.meta->>'amount')::decimal) as subscription_amount,
                COALESCE((al.meta->>'subscription_paid')::boolean, TRUE) as subscription_paid,
                (al.meta->>'payment_id')::int as payment_id,
                (al.meta->>'result_position')::int as result_position,
                al.meta->>'result_notes' as result_notes,
                al.performed_by,
                u.username as performed_by_name,
                al.created_at
            FROM student_activity_log al
            LEFT JOIN users u ON u.id = al.performed_by
            WHERE al.student_id = :student_id
              AND (al.activity_type = 'competition' OR (al.activity_type = 'payment' AND al.activity_subtype = 'competition_fee'))
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
              AND (activity_type = 'competition' OR (activity_type = 'payment' AND activity_subtype = 'competition_fee'))
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

    def search_activities(
        self,
        search_term: Optional[str] = None,
        activity_types: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        performed_by: Optional[int] = None,
        student_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[StudentActivityLog]:
        """Search activity logs with filters using raw SQL."""
        conditions = []
        params: Dict[str, Any] = {}

        if search_term:
            conditions.append("(description ILIKE :search_term OR meta::text ILIKE :search_term)")
            params["search_term"] = f"%{search_term}%"
        if activity_types:
            conditions.append("activity_type = ANY(:activity_types)")
            params["activity_types"] = activity_types
        if date_from:
            conditions.append("created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            conditions.append("created_at <= :date_to")
            params["date_to"] = date_to
        if performed_by is not None:
            conditions.append("performed_by = :performed_by")
            params["performed_by"] = performed_by
        if student_id is not None:
            conditions.append("student_id = :student_id")
            params["student_id"] = student_id

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        sql = f"""
            SELECT id, student_id, activity_type, activity_subtype,
                   reference_type, reference_id, description, meta,
                   performed_by, created_at
            FROM student_activity_log
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """
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

    def get_activity_summary(self, student_id: int) -> ActivitySummaryDTO:
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

        return ActivitySummaryDTO(
            student_id=student_id,
            total_activities=total,
            activities_by_type=by_type,
            first_activity_date=first_activity,
            last_activity_date=last_activity,
        )
