"""
app/api/schemas/enrollments/enrollment.py
─────────────────────────────────────────
Public-facing Enrollment DTOs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EnrollmentPublic(BaseModel):
    """
    Public enrollment profile returned by the API.
    Masks internals like `created_by` or raw metadata.
    """

    id: int
    student_id: int
    group_id: int
    level_number: int
    status: str
    amount_due: Optional[float] = None
    discount_applied: float = 0.0
    payment_status: Optional[str] = None  # "paid", "due", "partial"
    notes: Optional[str] = None
    enrolled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StudentEnrollmentSummaryPublic(BaseModel):
    """Public summary DTO for student enrollment in a group."""
    student_id: int
    student_name: str
    enrollment_id: int
    level_number: int
    status: str
    sessions_attended: int
    sessions_total: int
    payment_status: str  # "paid", "due", "partial"
    amount_due: float
    discount_applied: float

    model_config = {"from_attributes": True}
