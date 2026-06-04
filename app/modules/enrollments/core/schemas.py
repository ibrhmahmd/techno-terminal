from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.modules.enrollments.models.enrollment_models import EnrollmentBase


class EnrollStudentInput(BaseModel):
    student_id: int
    group_id: int
    amount_due: Optional[float] = None
    discount: float = 0.0
    notes: Optional[str] = None
    created_by: Optional[int] = None


class TransferStudentInput(BaseModel):
    from_enrollment_id: int
    to_group_id: int
    created_by: Optional[int] = None


class UpdateEnrollmentInput(BaseModel):
    amount_due: Optional[float] = None
    discount_applied: Optional[float] = None
    notes: Optional[str] = None


class UpdateEnrollmentResult(BaseModel):
    enrollment: "EnrollmentDTO"
    warnings: list[str] = []


class EnrollmentDTO(EnrollmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_name: Optional[str] = None
    course_name: Optional[str] = None
    instructor_name: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    enrollment_metadata: Optional[dict[str, Any]] = None
    payment_status: Optional[str] = None
    amount_remaining: Optional[float] = None


class EnrollmentCoreResult(BaseModel):
    enrollment: EnrollmentDTO
    capacity_exceeded: bool = False
