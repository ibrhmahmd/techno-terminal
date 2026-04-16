from typing import Optional, TYPE_CHECKING
from sqlalchemy.exc import IntegrityError
from fastapi import BackgroundTasks
from app.db.connection import get_session
from app.shared.audit_utils import apply_create_audit
from app.shared.datetime_utils import utc_now
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.services.student_crud_service import StudentCrudService
from app.modules.crm.services.activity_service import StudentActivityService
import app.modules.academics as acad_srv
from app.modules.academics.models.group_models import Group
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    EnrollmentDTO,
    StudentEnrollmentSummaryDTO,
)
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
import app.modules.enrollments.repositories.enrollment_repository as repo
from app.modules.finance.repositories.payment_repository import PaymentRepository

if TYPE_CHECKING:
    from app.modules.notifications.services.notification_service import NotificationService

class EnrollmentService:
    """Service for managing student enrollments."""

    def __init__(self, activity_svc: Optional[StudentActivityService] = None, notification_svc: Optional["NotificationService"] = None) -> None:
        self._student_crud_service: Optional[StudentCrudService] = None
        self._activity_svc = activity_svc
        self._notification_svc = notification_svc

    def _get_student_service(self) -> StudentCrudService:
        """Lazy initialization of StudentCrudService with fresh UnitOfWork."""
        if self._student_crud_service is None:
            uow = StudentUnitOfWork()
            uow.__enter__()
            self._student_crud_service = StudentCrudService(uow)
        return self._student_crud_service

    def enroll_student(
        self,
        data: EnrollStudentInput,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> tuple[EnrollmentDTO, bool]:
        """
        Enrolls a student in a group.
        Returns (enrollment, capacity_exceeded: bool).
        Cross-module validation is done via service calls (each opens its own read session).
        """
        student_svc = self._get_student_service()
        student = student_svc.get_by_id(data.student_id)
        if not student:
            raise NotFoundError(f"Student ID {data.student_id} not found.")
        if not student.is_active:
            raise BusinessRuleError(f"Student '{student.full_name}' is not active.")

        group = acad_srv.get_group_by_id(data.group_id)
        if not group:
            raise NotFoundError(f"Group ID {data.group_id} not found.")
        if group.status != "active":
            raise BusinessRuleError(f"Group '{group.name}' is not active (status: {group.status}).")

        try:
            with get_session() as session:
                existing = repo.get_active_enrollment(session, data.student_id, data.group_id)
                if existing:
                    raise ConflictError(f"'{student.full_name}' is already enrolled in this group (Enrollment ID: {existing.id}).")

                active_enrollments = repo.list_enrollments(session, group_id=data.group_id, status="active")
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

                # Log enrollment activity
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

                # Trigger Notification
                if self._notification_svc and background_tasks:
                    self._notification_svc.notify_enrollment(
                        created.id, student.id, group.id, background_tasks
                    )

                return EnrollmentDTO.model_validate(created), capacity_exceeded
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
            return EnrollmentDTO.model_validate(updated)


    def transfer_student(
        self, data: TransferStudentInput
    ) -> EnrollmentDTO:
        target_group = acad_srv.get_group_by_id(data.to_group_id)
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

            # Log enrollment change activity
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

            return EnrollmentDTO.model_validate(created)


    def drop_enrollment(self, enrollment_id: int, performed_by: Optional[int] = None) -> EnrollmentDTO:
        with get_session() as session:
            enrollment = repo.get_enrollment(session, enrollment_id)
            if not enrollment:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")
            updated = repo.update_enrollment_status(session, enrollment_id, "dropped")

            # Log enrollment change activity
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

            return EnrollmentDTO.model_validate(updated)


    def complete_enrollment(self, enrollment_id: int, performed_by: Optional[int] = None) -> EnrollmentDTO:
        with get_session() as session:
            enrollment = repo.get_enrollment(session, enrollment_id)
            if not enrollment:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")
            updated = repo.update_enrollment_status(session, enrollment_id, "completed")

            # Log enrollment change activity
            if self._activity_svc:
                from app.modules.crm.interfaces.dtos.log_enrollment_change_dto import LogEnrollmentChangeDTO
                self._activity_svc.log_enrollment_change(
                    LogEnrollmentChangeDTO(
                        student_id=enrollment.student_id,
                        enrollment_id=enrollment.id,
                        action="completed",
                        performed_by=performed_by,
                    )
                )

            return EnrollmentDTO.model_validate(updated)


    def get_group_roster(
        self, group_id: int, level_number: int | None = None
    ) -> list[EnrollmentDTO]:
        with get_session() as session:
            enrollments = repo.list_enrollments(
                session, group_id=group_id, level_number=level_number, status="active"
            )
            return [EnrollmentDTO.model_validate(e) for e in enrollments]


    def get_enrollments_summary_by_group(
        self, group_id: int, level_number: int | None = None
    ) -> list[StudentEnrollmentSummaryDTO]:
        """
        Get enrollment summary for all students in a group.
        Includes attendance counts and payment status.
        """
        with get_session() as session:
            from app.modules.enrollments.models.enrollment_models import Enrollment
            from app.modules.crm.models import Student
            from app.modules.academics.models import GroupLevel
            from sqlmodel import select
            from app.modules.attendance.repositories import attendance_repository

            # Get all enrollments for the group (excluding dropped by default)
            stmt = select(Enrollment, Student).join(
                Student, Enrollment.student_id == Student.id
            ).where(Enrollment.group_id == group_id)

            if level_number:
                stmt = stmt.where(Enrollment.level_number == level_number)
            else:
                # Get enrollments for the group's current level
                group = session.get(Group, group_id)
                if group:
                    stmt = stmt.where(Enrollment.level_number == group.level_number)

            # Exclude dropped enrollments
            stmt = stmt.where(Enrollment.status != "dropped")

            results = session.exec(stmt).all()

            summary_list = []
            for enrollment, student in results:
                # Get attendance summary
                attendance_summary = attendance_repository.get_enrollment_attendance(
                    session, enrollment.id
                )

                # Get sessions total from group level
                level = session.exec(
                    select(GroupLevel).where(
                        GroupLevel.group_id == group_id,
                        GroupLevel.level_number == enrollment.level_number
                    )
                ).first()
                sessions_total = level.sessions_planned if level else 0

                # Get actual payment status from v_enrollment_balance view
                pay_repo = PaymentRepository(session)
                balance_info = pay_repo.get_enrollment_balance(enrollment.id)
                payment_status = balance_info.status if balance_info else 'not_paid'
                amount_remaining = float(balance_info.balance) if balance_info else 0.0

                amount_due = float(enrollment.amount_due or 0)
                discount = float(enrollment.discount_applied or 0)

                summary = StudentEnrollmentSummaryDTO(
                    student_id=student.id,
                    student_name=student.full_name or "Unknown",
                    enrollment_id=enrollment.id,
                    level_number=enrollment.level_number,
                    status=enrollment.status,
                    sessions_attended=attendance_summary.sessions_attended,
                    sessions_total=sessions_total,
                    payment_status=payment_status,
                    amount_remaining=amount_remaining,
                    amount_due=amount_due,
                    discount_applied=discount,
                )
                summary_list.append(summary)

            return summary_list


    def get_student_enrollments(self, student_id: int) -> list[EnrollmentDTO]:
        with get_session() as session:
            enrollments = repo.get_enrollments_by_student(session, student_id)
            result = []
            for enrollment in enrollments:
                dto = EnrollmentDTO.model_validate(enrollment)
                # Enrich with payment status from v_enrollment_balance
                pay_repo = PaymentRepository(session)
                balance_info = pay_repo.get_enrollment_balance(enrollment.id)
                if balance_info:
                    dto.payment_status = balance_info.status
                    dto.amount_remaining = float(balance_info.balance)
                result.append(dto)
            return result
