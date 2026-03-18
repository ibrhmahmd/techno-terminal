from datetime import date
from typing import Sequence
from sqlmodel import Session, select
from app.modules.enrollments.models import Enrollment


def create_enrollment(session: Session, enrollment: Enrollment) -> Enrollment:
    session.add(enrollment)
    session.flush()
    return enrollment


def get_enrollment(session: Session, enrollment_id: int) -> Enrollment | None:
    return session.get(Enrollment, enrollment_id)


def get_active_enrollment(
    session: Session, student_id: int, group_id: int
) -> Enrollment | None:
    """Returns the active enrollment for a student in a group, or None."""
    stmt = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .where(Enrollment.group_id == group_id)
        .where(Enrollment.status == "active")
    )
    return session.exec(stmt).first()


def list_enrollments(
    session: Session,
    group_id: int | None = None,
    level_number: int | None = None,
    status: str | None = "active",
) -> Sequence[Enrollment]:
    stmt = select(Enrollment)
    if group_id is not None:
        stmt = stmt.where(Enrollment.group_id == group_id)
    if level_number is not None:
        stmt = stmt.where(Enrollment.level_number == level_number)
    if status is not None:
        stmt = stmt.where(Enrollment.status == status)
    return session.exec(stmt).all()


def update_enrollment_status(
    session: Session, enrollment_id: int, status: str
) -> Enrollment | None:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment:
        enrollment.status = status
        session.add(enrollment)
    return enrollment


def update_discount(
    session: Session, enrollment_id: int, discount: float
) -> Enrollment | None:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment:
        enrollment.discount_applied = discount
        session.add(enrollment)
    return enrollment


def get_enrollments_by_student(
    session: Session, student_id: int
) -> list[Enrollment]:
    """Returns all enrollments for a student across all groups and statuses."""
    stmt = select(Enrollment).where(Enrollment.student_id == student_id)
    return list(session.exec(stmt).all())


# ── RepositoryProtocol aliases ────────────────────────────────────────────────
get_by_id = get_enrollment
create = create_enrollment
list_all = list_enrollments
