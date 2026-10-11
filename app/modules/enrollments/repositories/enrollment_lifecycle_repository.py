from typing import Sequence
from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment


def get_active_enrollments_for_group_level(
    session: Session, group_id: int, level_number: int
) -> Sequence[Enrollment]:
    stmt = select(Enrollment).where(
        Enrollment.group_id == group_id,
        Enrollment.level_number == level_number,
        Enrollment.status == "active"
    )
    return session.exec(stmt).all()
