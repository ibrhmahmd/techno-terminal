from sqlmodel import Session
from app.modules.enrollments.analytics.repository import (
    get_roster_for_group_level,
    get_enrollments_by_group_with_students,
)
from app.modules.enrollments.analytics.schemas import (
    GroupRosterEntryDTO,
    GroupEnrollmentDTO,
)


class EnrollmentAnalyticsService:
    def get_roster_for_group_level(
        self, session: Session, group_id: int, level_number: int
    ) -> list[GroupRosterEntryDTO]:
        return get_roster_for_group_level(session, group_id, level_number)

    def get_enrollments_by_group_with_students(
        self, session: Session, group_id: int
    ) -> list[GroupEnrollmentDTO]:
        return get_enrollments_by_group_with_students(session, group_id)
