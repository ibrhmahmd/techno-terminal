from typing import Any, Optional, TYPE_CHECKING
from sqlalchemy.exc import IntegrityError
from fastapi import BackgroundTasks
from app.db.connection import get_session
from app.shared.audit_utils import apply_create_audit
from app.shared.datetime_utils import utc_now
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.services.student_crud_service import StudentCrudService
from app.modules.crm.services.activity_service import StudentActivityService
from app.modules.crm.models.student_models import StudentStatus
from app.modules.academics.group.core.service import GroupCoreService
from app.modules.academics.models.group_models import Group
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.core.schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    EnrollmentDTO,
    EnrollmentCoreResult,
)
import app.modules.enrollments.core.repository as repo
from app.modules.enrollments.directory.repository import list_enrollments
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError

if TYPE_CHECKING:
    from app.modules.notifications.services.notification_service import NotificationService


class EnrollmentCoreService:
    def __init__(self, activity_svc: Optional[StudentActivityService] = None, notification_svc: Optional["NotificationService"] = None) -> None:
        self._activity_svc = activity_svc
        self._notification_svc = notification_svc

    def enroll_student(
        self,
        data: EnrollStudentInput,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> EnrollmentCoreResult:
        with StudentUnitOfWork() as uow:
            student_svc = StudentCrudService(uow, self._activity_svc)
            student = student_svc.get_by_id(data.student_id)
        if not student:
            raise NotFoundError(f"Student ID {data.student_id} not found.")
        if student.status == StudentStatus.INACTIVE:
            raise BusinessRuleError(f"Student '{student.full_name}' is inactive and cannot be enrolled.")

        group = GroupCoreService().get_group_by_id(data.group_id)
        if not group:
            raise NotFoundError(f"Group ID {data.group_id} not found.")
        if group.status != "active":
            raise BusinessRuleError(f"Group '{group.name}' is not active (status: {group.status}).")

        try:
            with get_session() as session:
                existing = repo.get_active_enrollment(session, data.student_id, data.group_id)
                if existing:
                    raise ConflictError(f"'{student.full_name}' is already enrolled in this group (Enrollment ID: {existing.id}).")

                active_enrollments = list_enrollments(session, group_id=data.group_id, status="active")
                capacity_exceeded = (group.max_capacity is not None and len(active_enrollments) >= group.max_capacity)

                enrollment = Enrollment(
                    student_id=data.student_id,
                    group_id=data.group_id,
                    level_number=group.level_number,
                    enrolled_at=utc_now(),
                    amount_due=data.amount_due,
                    discount_applied=data.discount,
                    notes=data.notes,
                    created_by=data.created_by,
                    created_at=utc_now(),
                )
                created = repo.create_enrollment(session, enrollment)

                if student.status == StudentStatus.WAITING:
                    old_status = student.status
                    student.status = StudentStatus.ACTIVE
                    merged_student = session.merge(student)
                    session.add(merged_student)

                    if self._activity_svc:
                        from app.modules.crm.interfaces.dtos.log_status_change_dto import LogStatusChangeDTO
                        self._activity_svc.log_status_change(
                            LogStatusChangeDTO(
                                student_id=student.id,
                                old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
                                new_status=student.status.value if hasattr(student.status, 'value') else str(student.status),
                                performed_by=data.created_by,
                            )
                        )

                if self._activity_svc:
                    from app.modules.crm.interfaces.dtos.log_enrollment_dto import LogEnrollmentDTO
                    self._activity_svc.log_enrollment(
                        LogEnrollmentDTO(
                            student_id=created.student_id,
                            enrollment_id=created.id,
                            group_id=group.id,
                            group_name=group.name,
                            level_number=group.level_number,
                            performed_by=data.created_by,
                        )
                    )

                session.commit()
                session.refresh(created)
                if self._notification_svc and background_tasks:
                    self._notification_svc.enrollment.notify_enrollment_created(
                        student_id=student.id,
                        enrollment_id=created.id,
                        group_id=group.id,
                        level_number=group.level_number,
                        background_tasks=background_tasks,
                    )

                return EnrollmentCoreResult(
                    enrollment=EnrollmentDTO.model_validate(created),
                    capacity_exceeded=capacity_exceeded,
                )
        except IntegrityError:
            raise ConflictError(f"'{student.full_name}' was just enrolled in this group by another request. Please refresh and try again.")

    def apply_sibling_discount(
        self, enrollment_id: int, discount_amount: float = 50.0
    ) -> EnrollmentDTO:
        with get_session() as session:
            enrollment = repo.get_enrollment(session, enrollment_id)
            if not enrollment:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")
            if enrollment.status != "active":
                raise BusinessRuleError("Can only apply discount to active enrollments.")
            updated = repo.update_discount(session, enrollment_id, discount_amount)
            session.commit()
            session.refresh(updated)
            return EnrollmentDTO.model_validate(updated)

    def transfer_student(
        self,
        data: TransferStudentInput,
        background_tasks: Optional[Any] = None,
    ) -> EnrollmentDTO:
        target_group = GroupCoreService().get_group_by_id(data.to_group_id)
        if not target_group:
            raise NotFoundError(f"Target group {data.to_group_id} not found.")
        if target_group.status != "active":
            raise BusinessRuleError(f"Target group '{target_group.name}' is not active.")

        with get_session() as session:
            source = repo.get_enrollment(session, data.from_enrollment_id)
            if not source:
                raise NotFoundError(f"Source enrollment {data.from_enrollment_id} not found.")
            if source.status != "active":
                raise BusinessRuleError("Can only transfer an active enrollment.")

            repo.update_enrollment_status(session, data.from_enrollment_id, "transferred")

            new_enrollment = Enrollment(
                student_id=source.student_id,
                group_id=data.to_group_id,
                level_number=target_group.level_number,
                enrolled_at=utc_now(),
                amount_due=source.amount_due,
                discount_applied=source.discount_applied,
                transferred_from=data.from_enrollment_id,
                created_by=data.created_by,
            )
            apply_create_audit(new_enrollment)
            created = repo.create_enrollment(session, new_enrollment)

            if self._activity_svc:
                from app.modules.crm.interfaces.dtos.log_enrollment_change_dto import LogEnrollmentChangeDTO
                self._activity_svc.log_enrollment_change(
                    LogEnrollmentChangeDTO(
                        student_id=source.student_id,
                        enrollment_id=created.id,
                        action="transferred",
                        old_group_id=source.group_id,
                        new_group_id=data.to_group_id,
                        performed_by=data.created_by,
                    )
                )

            session.commit()
            session.refresh(created)
            if self._notification_svc and background_tasks:
                self._notification_svc.enrollment.notify_enrollment_transferred(
                    student_id=source.student_id,
                    from_enrollment_id=data.from_enrollment_id,
                    to_enrollment_id=created.id,
                    from_group_id=source.group_id,
                    to_group_id=data.to_group_id,
                    transferred_by=data.created_by,
                    background_tasks=background_tasks,
                )

            return EnrollmentDTO.model_validate(created)

    def drop_enrollment(
        self,
        enrollment_id: int,
        performed_by: Optional[int] = None,
        reason: Optional[str] = None,
        background_tasks: Optional[Any] = None,
    ) -> EnrollmentDTO:
        with get_session() as session:
            enrollment = repo.get_enrollment(session, enrollment_id)
            if not enrollment:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")

            group_id = enrollment.group_id
            student_id = enrollment.student_id

            updated = repo.update_enrollment_status(session, enrollment_id, "dropped")

            if self._activity_svc:
                from app.modules.crm.interfaces.dtos.log_enrollment_change_dto import LogEnrollmentChangeDTO
                self._activity_svc.log_enrollment_change(
                    LogEnrollmentChangeDTO(
                        student_id=enrollment.student_id,
                        enrollment_id=enrollment.id,
                        action="dropped",
                        performed_by=performed_by,
                    )
                )

            session.commit()
            session.refresh(updated)
            if self._notification_svc and background_tasks:
                self._notification_svc.enrollment.notify_enrollment_dropped(
                    student_id=student_id,
                    enrollment_id=enrollment_id,
                    group_id=group_id,
                    reason=reason,
                    dropped_by=performed_by,
                    background_tasks=background_tasks,
                )

            return EnrollmentDTO.model_validate(updated)
