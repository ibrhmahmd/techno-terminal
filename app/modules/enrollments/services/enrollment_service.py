from sqlalchemy.exc import IntegrityError
from app.db.connection import get_session
from app.shared.audit_utils import apply_create_audit
from app.shared.datetime_utils import utc_now
from app.modules.crm import crm_service as crm_srv
import app.modules.academics as acad_srv
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    EnrollmentDTO,
)
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
from app.modules.enrollments.repositories import enrollment_repository as repo

class EnrollmentService:
    def enroll_student(
        self,
        data: EnrollStudentInput,
    ) -> tuple[EnrollmentDTO, bool]:
        """
        Enrolls a student in a group.
        Returns (enrollment, capacity_exceeded: bool).
        Cross-module validation is done via service calls (each opens its own read session).
        """
        student = crm_srv.get_student_by_id(data.student_id)
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
            return EnrollmentDTO.model_validate(created)


    def drop_enrollment(self, enrollment_id: int) -> EnrollmentDTO:
        with get_session() as session:
            enrollment = repo.get_enrollment(session, enrollment_id)
            if not enrollment:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")
            updated = repo.update_enrollment_status(session, enrollment_id, "dropped")
            return EnrollmentDTO.model_validate(updated)


    def complete_enrollment(self, enrollment_id: int) -> EnrollmentDTO:
        with get_session() as session:
            enrollment = repo.get_enrollment(session, enrollment_id)
            if not enrollment:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")
            updated = repo.update_enrollment_status(session, enrollment_id, "completed")
            return EnrollmentDTO.model_validate(updated)


    def get_group_roster(
        self, group_id: int, level_number: int | None = None
    ) -> list[EnrollmentDTO]:
        with get_session() as session:
            enrollments = repo.list_enrollments(
                session, group_id=group_id, level_number=level_number, status="active"
            )
            return [EnrollmentDTO.model_validate(e) for e in enrollments]


    def get_student_enrollments(self, student_id: int) -> list[EnrollmentDTO]:
        with get_session() as session:
            enrollments = repo.get_enrollments_by_student(session, student_id)
            return [EnrollmentDTO.model_validate(e) for e in enrollments]
