from typing import Sequence
from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.shared.audit_utils import apply_update_audit


def create_enrollment(session: Session, enrollment: Enrollment) -> Enrollment:
    session.add(enrollment)
    session.flush()
    return enrollment


def get_enrollment(session: Session, enrollment_id: int) -> Enrollment | None:
    return session.get(Enrollment, enrollment_id)


def get_active_enrollment(
    session: Session, student_id: int, group_id: int
) -> Enrollment | None:
    stmt = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .where(Enrollment.group_id == group_id)
        .where(Enrollment.status == "active")
    )
    return session.exec(stmt).first()


def update_enrollment_status(
    session: Session, enrollment_id: int, status: str
) -> Enrollment | None:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment:
        enrollment.status = status
        apply_update_audit(enrollment)
        session.add(enrollment)
    return enrollment


def update_discount(
    session: Session, enrollment_id: int, discount: float
) -> Enrollment | None:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment:
        enrollment.discount_applied = discount
        apply_update_audit(enrollment)
        session.add(enrollment)
    return enrollment
