from typing import Protocol, runtime_checkable
from sqlmodel import Session
from app.modules.enrollments.lifecycle.schemas import (
    MigrateEnrollmentsDTO,
    EnrollmentMigrationResult,
)


@runtime_checkable
class EnrollmentLifecycleInterface(Protocol):
    def migrate_enrollments_to_next_level(
        self,
        session: Session,
        data: MigrateEnrollmentsDTO
    ) -> EnrollmentMigrationResult: ...
