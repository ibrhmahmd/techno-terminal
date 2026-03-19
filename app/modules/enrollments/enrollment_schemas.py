"""
app/modules/enrollments/enrollment_schemas.py
────────────────────────────────────────────────
Typed input DTOs for the Enrollments service layer.
"""
from typing import Optional
from pydantic import BaseModel


class EnrollStudentInput(BaseModel):
    """Input for enrollment_service.enroll_student()."""
    student_id: int
    group_id: int
    amount_due: Optional[float] = None
    discount: float = 0.0
    notes: Optional[str] = None
    created_by: Optional[int] = None


class TransferStudentInput(BaseModel):
    """Input for enrollment_service.transfer_student()."""
    from_enrollment_id: int
    to_group_id: int
    created_by: Optional[int] = None
