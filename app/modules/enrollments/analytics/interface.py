from typing import Protocol, runtime_checkable
from sqlmodel import Session
from app.modules.enrollments.analytics.schemas import (
    GroupRosterEntryDTO,
    GroupEnrollmentDTO,
)


@runtime_checkable
class EnrollmentAnalyticsInterface(Protocol):
    def get_roster_for_group_level(
        self, session: Session, group_id: int, level_number: int
    ) -> list[GroupRosterEntryDTO]: ...

    def get_enrollments_by_group_with_students(
        self, session: Session, group_id: int
    ) -> list[GroupEnrollmentDTO]: ...
