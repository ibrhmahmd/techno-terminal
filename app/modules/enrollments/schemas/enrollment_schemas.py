"""
app/modules/enrollments/schemas/enrollment_schemas.py
────────────────────────────────────────────────
Typed DTOs for the Enrollments layer.
"""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel
from app.modules.enrollments.models.enrollment_models import EnrollmentBase


class EnrollStudentInput(BaseModel):
    """Input DTO for enrolling a student."""
    student_id: int
    group_id: int
    amount_due: Optional[float] = None
    discount: float = 0.0
    notes: Optional[str] = None
    created_by: Optional[int] = None


class TransferStudentInput(BaseModel):
    """Input DTO for transferring a student."""
    from_enrollment_id: int
    to_group_id: int
    created_by: Optional[int] = None


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentRead(EnrollmentBase):
    id: int
    enrolled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EnrollmentDTO(EnrollmentBase):
    """Output DTO for enrollment responses representing a detached, safe view."""
    id: int
    enrolled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    enrollment_metadata: Optional[dict[str, Any]] = None
