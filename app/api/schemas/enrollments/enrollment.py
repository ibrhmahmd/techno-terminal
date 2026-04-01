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
    notes: Optional[str] = None
    enrolled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
