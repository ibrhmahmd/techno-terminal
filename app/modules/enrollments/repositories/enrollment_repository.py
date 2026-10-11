from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.shared.audit_utils import apply_update_audit


class EnrollmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_enrollment(self, enrollment: Enrollment) -> Enrollment:
        self._session.add(enrollment)
        self._session.flush()
        return enrollment

    def get_enrollment(self, enrollment_id: int) -> Enrollment | None:
        return self._session.get(Enrollment, enrollment_id)

    def get_active_enrollment(
        self, student_id: int, group_id: int
    ) -> Enrollment | None:
        stmt = (
            select(Enrollment)
            .where(Enrollment.student_id == student_id)
            .where(Enrollment.group_id == group_id)
            .where(Enrollment.status == "active")
        )
        return self._session.exec(stmt).first()

    def update_enrollment_status(
        self, enrollment_id: int, status: str
    ) -> Enrollment | None:
        enrollment = self._session.get(Enrollment, enrollment_id)
        if enrollment:
            enrollment.status = status
            apply_update_audit(enrollment)
            self._session.add(enrollment)
        return enrollment

    def update_discount(
        self, enrollment_id: int, discount: float
    ) -> Enrollment | None:
        enrollment = self._session.get(Enrollment, enrollment_id)
        if enrollment:
            enrollment.discount_applied = discount
            apply_update_audit(enrollment)
            self._session.add(enrollment)
        return enrollment

    def update_enrollment_fields(
        self, enrollment_id: int, updates: dict
    ) -> Enrollment | None:
        enrollment = self._session.get(Enrollment, enrollment_id)
        if enrollment:
            for field, value in updates.items():
                setattr(enrollment, field, value)
            apply_update_audit(enrollment)
            self._session.add(enrollment)
        return enrollment
