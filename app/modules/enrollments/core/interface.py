from typing import Optional, Protocol, runtime_checkable
from fastapi import BackgroundTasks
from app.modules.enrollments.core.schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    EnrollmentDTO,
    EnrollmentCoreResult,
)


@runtime_checkable
class EnrollmentCoreInterface(Protocol):
    def enroll_student(
        self,
        data: EnrollStudentInput,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> EnrollmentCoreResult: ...

    def apply_sibling_discount(
        self, enrollment_id: int, discount_amount: float = 50.0
    ) -> EnrollmentDTO: ...

    def transfer_student(
        self,
        data: TransferStudentInput,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> EnrollmentDTO: ...

    def drop_enrollment(
        self,
        enrollment_id: int,
        performed_by: Optional[int] = None,
        reason: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> EnrollmentDTO: ...
