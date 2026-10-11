from typing import Sequence
from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment


class EnrollmentDirectoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_enrollments(
        self,
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
        return self._session.exec(stmt).all()

    def get_enrollments_by_student(self, student_id: int) -> list[Enrollment]:
        stmt = select(Enrollment).where(Enrollment.student_id == student_id)
        return list(self._session.exec(stmt).all())
