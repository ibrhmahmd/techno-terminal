"""Hard deletes of E2E test data in enrollments' own tables (#218). Staging only."""
from sqlalchemy import delete, or_, select
from sqlmodel import Session

from app.modules.enrollments.models import Enrollment, EnrollmentLevelHistory


class EnrollmentsE2EPurgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_enrollment_ids(self, student_ids: list[int], group_ids: list[int]) -> list[int]:
        stmt = select(Enrollment.id).where(or_(
            Enrollment.student_id.in_(student_ids), Enrollment.group_id.in_(group_ids),
        ))
        return list(self._session.execute(stmt).scalars())

    def delete_level_history(
        self, enrollment_ids: list[int], student_ids: list[int], level_ids: list[int]
    ) -> int:
        return self._session.execute(delete(EnrollmentLevelHistory).where(or_(
            EnrollmentLevelHistory.enrollment_id.in_(enrollment_ids),
            EnrollmentLevelHistory.student_id.in_(student_ids),
            EnrollmentLevelHistory.group_level_id.in_(level_ids),
        ))).rowcount

    def delete_enrollments(self, enrollment_ids: list[int]) -> int:
        return self._session.execute(
            delete(Enrollment).where(Enrollment.id.in_(enrollment_ids))
        ).rowcount
