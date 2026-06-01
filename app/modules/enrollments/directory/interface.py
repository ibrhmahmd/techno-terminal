from typing import Protocol, runtime_checkable
from app.modules.enrollments.core.schemas import EnrollmentDTO
from app.modules.enrollments.directory.schemas import StudentEnrollmentSummaryDTO


@runtime_checkable
class EnrollmentDirectoryInterface(Protocol):
    def get_student_enrollments(self, student_id: int) -> list[EnrollmentDTO]: ...

    def get_enrollments_summary_by_group(
        self, group_id: int, level_number: int | None = None
    ) -> list[StudentEnrollmentSummaryDTO]: ...
