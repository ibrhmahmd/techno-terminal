import logging
from typing import Optional
from sqlalchemy.exc import IntegrityError
from app.db.uow import UnitOfWork
from app.shared.audit_utils import apply_create_audit
from app.shared.datetime_utils import utc_now
from app.modules.crm.models.student_models import StudentStatus
from app.modules.crm import (
    StudentCrudService,
    StudentActivityService,
    LogStatusChangeDTO,
    LogEnrollmentDTO,
    LogEnrollmentChangeDTO,
)
from app.modules.academics import GroupCoreService
from app.modules.academics.models.group_models import Group
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.ports import EnrollmentNotifier
from app.modules.enrollments.schemas.enrollment_schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    UpdateEnrollmentInput,
    UpdateEnrollmentResult,
    EnrollmentDTO,
    EnrollmentCoreResult,
)
from app.modules.enrollments.repositories.enrollment_repository import (
    EnrollmentRepository,
)
from app.modules.enrollments.repositories.enrollment_directory_repository import (
    EnrollmentDirectoryRepository,
)
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError

logger = logging.getLogger(__name__)


class EnrollmentService:
    def __init__(
        self,
        uow: UnitOfWork,
        activity_svc: Optional["StudentActivityService"] = None,
        notifier: Optional[EnrollmentNotifier] = None,
    ) -> None:
        self._uow = uow
        self._activity_svc = (
            activity_svc if activity_svc is not None else StudentActivityService(uow)
        )
        self._notifier = notifier
        self._enrollments = EnrollmentRepository(uow.session)
        self._directory = EnrollmentDirectoryRepository(uow.session)

    def _notify(self, method: str, **kwargs) -> None:
        """Call the notifier after commit; failures are logged, never raised."""
        if self._notifier is None:
            return
        try:
            getattr(self._notifier, method)(**kwargs)
        except Exception:
            logger.exception("Enrollment notifier %s failed", method)

    def get_active_enrollment(
        self, student_id: int, group_id: int
    ) -> Optional[Enrollment]:
        """Read-only lookup exposed for cross-module callers (facade method)."""
        return self._enrollments.get_active_enrollment(student_id, group_id)

    def enroll_student(
        self,
        data: EnrollStudentInput,
    ) -> EnrollmentCoreResult:
        uow = self._uow
        session = uow.session
        student_svc = StudentCrudService(uow, self._activity_svc)
        student = student_svc.get_by_id(data.student_id)
        if not student:
            raise NotFoundError(f"Student ID {data.student_id} not found.")
        if student.status == StudentStatus.INACTIVE:
            raise BusinessRuleError(f"Student '{student.full_name}' is inactive and cannot be enrolled.")

        group = GroupCoreService(uow).get_group_by_id(data.group_id)
        if not group:
            raise NotFoundError(f"Group ID {data.group_id} not found.")
        if group.status != "active":
            raise BusinessRuleError(f"Group '{group.name}' is not active (status: {group.status}).")

        try:
            existing = self._enrollments.get_active_enrollment(data.student_id, data.group_id)
            if existing:
                raise ConflictError(f"'{student.full_name}' is already enrolled in this group (Enrollment ID: {existing.id}).")

            active_enrollments = self._directory.list_enrollments(group_id=data.group_id, status="active")
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
            created = self._enrollments.create_enrollment(enrollment)

            if student.status == StudentStatus.WAITING:
                old_status = student.status
                student.status = StudentStatus.ACTIVE
                merged_student = session.merge(student)
                session.add(merged_student)

                if self._activity_svc:
                    self._activity_svc.log_status_change(
                        LogStatusChangeDTO(
                            student_id=student.id,
                            old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
                            new_status=student.status.value if hasattr(student.status, 'value') else str(student.status),
                            performed_by=data.created_by,
                        )
                    )

            if self._activity_svc:
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

            uow.commit()
            session.refresh(created)
            self._notify(
                "enrollment_created",
                student_id=student.id,
                enrollment_id=created.id,
                group_id=group.id,
                level_number=group.level_number,
            )

            return EnrollmentCoreResult(
                enrollment=EnrollmentDTO.model_validate(created),
                capacity_exceeded=capacity_exceeded,
            )
        except IntegrityError:
            raise ConflictError(f"'{student.full_name}' was just enrolled in this group by another request. Please refresh and try again.")

    def update_enrollment(
        self,
        enrollment_id: int,
        data: UpdateEnrollmentInput,
        performed_by: Optional[int] = None,
    ) -> UpdateEnrollmentResult:
        session = self._uow.session
        enrollment = self._enrollments.get_enrollment(enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found.")
        if enrollment.status in ("dropped", "transferred"):
            raise BusinessRuleError("Cannot edit dropped or transferred enrollments.")

        updates = {}
        if "amount_due" in data.model_fields_set:
            if data.amount_due is not None and data.amount_due < 0:
                raise BusinessRuleError("Amount due cannot be negative.")
            updates["amount_due"] = data.amount_due

        if "discount_applied" in data.model_fields_set:
            if data.discount_applied is not None and data.discount_applied < 0:
                raise BusinessRuleError("Discount applied cannot be negative.")
            updates["discount_applied"] = data.discount_applied

        if "notes" in data.model_fields_set:
            updates["notes"] = data.notes

        if not updates:
            return UpdateEnrollmentResult(enrollment=EnrollmentDTO.model_validate(enrollment))

        warnings = []

        # Check for financial conflicts if financial fields are changing
        if "amount_due" in updates or "discount_applied" in updates:
            if self._enrollments.has_payments(enrollment_id):
                warnings.append("Note: Payments already exist for this enrollment. Verify if adjustments are needed.")

        # Audit logging
        metadata = dict(enrollment.enrollment_metadata) if enrollment.enrollment_metadata else {}
        edit_history = metadata.get("edit_history", [])

        changes = {}
        changes_summary_parts = []

        def format_field_name(f: str) -> str:
            return f.replace("_", " ").title()

        for field, new_val in updates.items():
            old_val = getattr(enrollment, field)
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
                old_display = f"{old_val} EGP" if "amount" in field or "discount" in field else old_val
                new_display = f"{new_val} EGP" if "amount" in field or "discount" in field else new_val
                changes_summary_parts.append(f"• {format_field_name(field)}: {old_display} ➔ {new_display}")

        if changes:
            edit_entry = {
                "timestamp": utc_now().isoformat(),
                "performed_by": performed_by,
                "changes": changes
            }
            edit_history.append(edit_entry)
            metadata["edit_history"] = edit_history
            updates["enrollment_metadata"] = metadata

            updated = self._enrollments.update_enrollment_fields(enrollment_id, updates)

            if self._activity_svc:
                self._activity_svc.log_enrollment_change(
                    LogEnrollmentChangeDTO(
                        student_id=updated.student_id,
                        enrollment_id=updated.id,
                        action="financials_updated",
                        changes_summary="\n".join(changes_summary_parts),
                        performed_by=performed_by,
                    )
                )

            self._uow.commit()
            session.refresh(updated)

            if "amount_due" in changes or "discount_applied" in changes:
                self._notify(
                    "enrollment_updated",
                    student_id=updated.student_id,
                    enrollment_id=updated.id,
                    group_id=updated.group_id,
                    changes_summary="<br>".join(changes_summary_parts),
                    performed_by=performed_by,
                )
            return UpdateEnrollmentResult(enrollment=EnrollmentDTO.model_validate(updated), warnings=warnings)

        return UpdateEnrollmentResult(enrollment=EnrollmentDTO.model_validate(enrollment))

    def apply_sibling_discount(
        self, enrollment_id: int, discount_amount: float = 50.0
    ) -> EnrollmentDTO:
        session = self._uow.session
        enrollment = self._enrollments.get_enrollment(enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found.")
        if enrollment.status != "active":
            raise BusinessRuleError("Can only apply discount to active enrollments.")
        updated = self._enrollments.update_discount(enrollment_id, discount_amount)
        self._uow.commit()
        session.refresh(updated)
        return EnrollmentDTO.model_validate(updated)

    def transfer_student(
        self,
        data: TransferStudentInput,
    ) -> EnrollmentDTO:
        uow = self._uow
        session = uow.session
        target_group = GroupCoreService(uow).get_group_by_id(data.to_group_id)
        if target_group.status != "active":
            raise BusinessRuleError(f"Target group '{target_group.name}' is not active.")

        source = self._enrollments.get_enrollment(data.from_enrollment_id)
        if not source:
            raise NotFoundError(f"Source enrollment {data.from_enrollment_id} not found.")
        if source.status != "active":
            raise BusinessRuleError("Can only transfer an active enrollment.")

        self._enrollments.update_enrollment_status(data.from_enrollment_id, "transferred")

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
        created = self._enrollments.create_enrollment(new_enrollment)

        if self._activity_svc:
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

        uow.commit()
        session.refresh(created)
        self._notify(
            "enrollment_transferred",
            student_id=source.student_id,
            from_enrollment_id=data.from_enrollment_id,
            to_enrollment_id=created.id,
            from_group_id=source.group_id,
            to_group_id=data.to_group_id,
            transferred_by=data.created_by,
        )

        return EnrollmentDTO.model_validate(created)

    def drop_enrollment(
        self,
        enrollment_id: int,
        performed_by: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> EnrollmentDTO:
        session = self._uow.session
        enrollment = self._enrollments.get_enrollment(enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found.")

        group_id = enrollment.group_id
        student_id = enrollment.student_id

        updated = self._enrollments.update_enrollment_status(enrollment_id, "dropped")

        if self._activity_svc:
            self._activity_svc.log_enrollment_change(
                LogEnrollmentChangeDTO(
                    student_id=enrollment.student_id,
                    enrollment_id=enrollment.id,
                    action="dropped",
                    changes_summary=reason,
                    performed_by=performed_by,
                )
            )

        self._uow.commit()
        session.refresh(updated)
        self._notify(
            "enrollment_dropped",
            student_id=student_id,
            enrollment_id=enrollment_id,
            group_id=group_id,
            reason=reason,
            dropped_by=performed_by,
        )

        return EnrollmentDTO.model_validate(updated)
