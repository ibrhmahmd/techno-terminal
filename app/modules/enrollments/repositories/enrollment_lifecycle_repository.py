from typing import Sequence
from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment


class EnrollmentLifecycleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active_enrollments_for_group_level(
        self, group_id: int, level_number: int
    ) -> Sequence[Enrollment]:
        stmt = select(Enrollment).where(
            Enrollment.group_id == group_id,
            Enrollment.level_number == level_number,
            Enrollment.status == "active"
        )
        return self._session.exec(stmt).all()
