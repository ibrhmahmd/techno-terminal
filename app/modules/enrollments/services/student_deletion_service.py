from app.db.uow import UnitOfWork
from app.modules.crm import LogEnrollmentChangeDTO, StudentActivityService, StudentCrudService
from app.modules.enrollments.repositories.enrollment_repository import EnrollmentRepository


class StudentDeletionService:
    """Soft-deletes a student and drops their active enrollments in one transaction (#175).

    Lives in enrollments because the use case writes crm and enrollments tables (ADR-0006).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._activity = StudentActivityService(uow)
        self._students = StudentCrudService(uow, activity_svc=self._activity)
        self._enrollments = EnrollmentRepository(uow.session)

    def delete_student(self, student_id: int, deleted_by: int) -> bool:
        """Returns False when the student is missing or already deleted."""
        if not self._students.soft_delete_student(student_id, deleted_by):
            return False
        for enrollment in self._enrollments.get_active_enrollments_for_student(student_id):
            self._enrollments.update_enrollment_status(enrollment.id, "dropped")
            self._activity.log_enrollment_change(
                LogEnrollmentChangeDTO(
                    student_id=student_id,
                    enrollment_id=enrollment.id,
                    action="dropped",
                    changes_summary="Student deleted",
                    performed_by=deleted_by,
                )
            )
        self._uow.commit()
        return True
