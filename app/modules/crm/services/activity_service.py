"""
app/modules/crm/services/activity_service.py
────────────────────────────────────────────
Student activity logging and history service.
Integrates with CRM services for automatic activity tracking.
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.interfaces.dtos.activity_log_dto import ActivityLogDTO
from app.modules.crm.interfaces.dtos.timeline_filter_dto import TimelineFilterDTO
from app.modules.crm.interfaces.dtos.activity_summary_dto import ActivitySummaryDTO
from app.modules.crm.interfaces.dtos.log_registration_dto import LogRegistrationDTO
from app.modules.crm.interfaces.dtos.log_status_change_dto import LogStatusChangeDTO
from app.modules.crm.interfaces.dtos.log_enrollment_dto import LogEnrollmentDTO
from app.modules.crm.interfaces.dtos.log_enrollment_change_dto import LogEnrollmentChangeDTO
from app.modules.crm.interfaces.dtos.log_payment_dto import LogPaymentDTO
from app.modules.crm.interfaces.dtos.log_deletion_dto import LogDeletionDTO
from app.modules.crm.interfaces.dtos.log_note_added_dto import LogNoteAddedDTO
from app.modules.crm.interfaces.dtos.log_competition_registration_dto import LogCompetitionRegistrationDTO
from app.modules.crm.interfaces.dtos import (
    EnrollmentHistoryDTO,
    StatusHistoryDTO,
    CompetitionHistoryDTO,
)
from app.modules.crm.models.activity_models import StudentActivityLog


class StudentActivityService:
    """
    Service for logging and querying student activities.
    Follows SOLID architecture with UnitOfWork pattern.
    """

    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow

    # ── Logging Methods (Auto-called by other services) ────────────────────

    def log_registration(self, dto: LogRegistrationDTO) -> StudentActivityLog:
        """Log student registration activity."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="registration",
            activity_subtype="student_created",
            reference_type="student",
            reference_id=dto.student_id,
            description=f"Student '{dto.student_name}' registered",
            metadata={"student_name": dto.student_name},
            performed_by=dto.performed_by,
        )

    def log_status_change(self, dto: LogStatusChangeDTO) -> StudentActivityLog:
        """Log student status change."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="status_change",
            activity_subtype=f"{dto.old_status}_to_{dto.new_status}",
            reference_type="student",
            reference_id=dto.student_id,
            description=f"Status changed from '{dto.old_status}' to '{dto.new_status}'",
            metadata={
                "old_status": dto.old_status,
                "new_status": dto.new_status,
            },
            performed_by=dto.performed_by,
        )

    def log_enrollment(self, dto: LogEnrollmentDTO) -> StudentActivityLog:
        """Log student enrollment activity."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="enrollment",
            activity_subtype="enrollment_created",
            reference_type="enrollment",
            reference_id=dto.enrollment_id,
            description=f"Enrolled in group '{dto.group_name}' (Level {dto.level_number})",
            metadata={
                "enrollment_id": dto.enrollment_id,
                "group_id": dto.group_id,
                "group_name": dto.group_name,
                "level_number": dto.level_number,
            },
            performed_by=dto.performed_by,
        )

    def log_enrollment_change(self, dto: LogEnrollmentChangeDTO) -> StudentActivityLog:
        """Log enrollment lifecycle changes."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="enrollment_change",
            activity_subtype=dto.action,
            reference_type="enrollment",
            reference_id=dto.enrollment_id,
            description=f"Enrollment {dto.action}",
            metadata={
                "enrollment_id": dto.enrollment_id,
                "action": dto.action,
                "old_group_id": dto.old_group_id,
                "new_group_id": dto.new_group_id,
            },
            performed_by=dto.performed_by,
        )

    def log_payment(self, dto: LogPaymentDTO) -> StudentActivityLog:
        """Log payment activity."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="payment",
            activity_subtype=dto.payment_type,
            reference_type="payment",
            reference_id=dto.payment_id,
            description=f"Payment of {dto.amount} received",
            metadata={
                "payment_id": dto.payment_id,
                "amount": str(dto.amount),
                "payment_type": dto.payment_type,
            },
            performed_by=dto.performed_by,
        )

    def log_deletion(self, dto: LogDeletionDTO) -> StudentActivityLog:
        """Log student deletion activity."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="deletion",
            activity_subtype="student_deleted",
            reference_type="student",
            reference_id=dto.student_id,
            description=f"Student '{dto.student_name}' deleted",
            metadata={
                "student_id": dto.student_id,
                "student_name": dto.student_name,
                "deleted_at": datetime.utcnow().isoformat(),
            },
            performed_by=dto.performed_by,
        )

    def log_note_added(self, dto: LogNoteAddedDTO) -> StudentActivityLog:
        """Log note/communication activity."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="note",
            activity_subtype=dto.note_type,
            reference_type="note",
            reference_id=dto.note_id,
            description=f"{dto.note_type.capitalize()} note added",
            metadata={
                "note_id": dto.note_id,
                "note_type": dto.note_type,
            },
            performed_by=dto.performed_by,
        )

    def log_competition_registration(self, dto: LogCompetitionRegistrationDTO) -> StudentActivityLog:
        """Log competition registration activity."""
        return self._uow.activities.create_activity_log(
            student_id=dto.student_id,
            activity_type="competition",
            activity_subtype="registered",
            reference_type="competition",
            reference_id=dto.competition_id,
            description=f"Registered for competition '{dto.competition_name}'",
            metadata={
                "competition_id": dto.competition_id,
                "competition_name": dto.competition_name,
            },
            performed_by=dto.performed_by,
        )

    # ── Query Methods ───────────────────────────────────────────────────

    def get_student_timeline(
        self,
        student_id: int,
        filters: TimelineFilterDTO,
    ) -> List[ActivityLogDTO]:
        """Get activity timeline for a student."""
        logs = self._uow.activities.get_student_activity_timeline(
            student_id=student_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            limit=filters.limit,
        )
        return [self._map_to_dto(log) for log in logs]

    def get_recent_activities(self, days: int = 7) -> List[ActivityLogDTO]:
        """Get recent activities across all students."""
        logs = self._uow.activities.get_recent_activities(days=days)
        return [self._map_to_dto(log) for log in logs]

    def get_activity_summary(self, student_id: int) -> ActivitySummaryDTO:
        """Get activity summary for a student."""
        summary = self._uow.activities.get_activity_summary(student_id)
        return ActivitySummaryDTO(
            student_id=student_id,
            total_activities=summary["total_activities"],
            activities_by_type=summary["activities_by_type"],
            first_activity_date=summary["first_activity_date"],
            last_activity_date=summary["last_activity_date"],
        )

    def get_enrollment_history(
        self, student_id: int, limit: int = 50, offset: int = 0
    ) -> Tuple[List[EnrollmentHistoryDTO], int]:
        """Get enrollment lifecycle history for a student with pagination."""
        return self._uow.activities.get_enrollment_history_by_student(student_id, limit, offset)

    def get_status_history(
        self, student_id: int, limit: int = 50, offset: int = 0
    ) -> Tuple[List[StatusHistoryDTO], int]:
        """Get status change history for a student with pagination."""
        return self._uow.activities.get_status_history_by_student(student_id, limit, offset)

    def get_competition_history(
        self, student_id: int, limit: int = 50, offset: int = 0
    ) -> Tuple[List[CompetitionHistoryDTO], int]:
        """Get competition participation history for a student with pagination."""
        return self._uow.activities.get_competition_history_by_student(student_id, limit, offset)

    # ── Private Helpers ──────────────────────────────────────────────────

    def _map_to_dto(self, log: StudentActivityLog) -> ActivityLogDTO:
        """Map database model to DTO."""
        return ActivityLogDTO(
            id=log.id,
            student_id=log.student_id,
            activity_type=log.activity_type,
            activity_subtype=log.activity_subtype,
            reference_type=log.reference_type,
            reference_id=log.reference_id,
            description=log.description,
            metadata=log.meta or {},
            performed_by=log.performed_by,
            performed_by_name=None,  # Enriched separately if needed
            created_at=log.created_at,
        )
