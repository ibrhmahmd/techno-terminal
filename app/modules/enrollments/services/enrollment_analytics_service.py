from app.db.uow import UnitOfWork
from app.modules.enrollments.repositories.enrollment_analytics_repository import (
    EnrollmentAnalyticsRepository,
)
from app.modules.enrollments.schemas.enrollment_analytics_schemas import (
    GroupRosterEntryDTO,
    GroupEnrollmentDTO,
)


class EnrollmentAnalyticsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = EnrollmentAnalyticsRepository(uow.session)

    def get_roster_for_group_level(
        self, group_id: int, level_number: int
    ) -> list[GroupRosterEntryDTO]:
        return self._repo.get_roster_for_group_level(group_id, level_number)

    def get_enrollments_by_group_with_students(
        self, group_id: int
    ) -> list[GroupEnrollmentDTO]:
        return self._repo.get_enrollments_by_group_with_students(group_id)
