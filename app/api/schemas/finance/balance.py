"""
app/api/schemas/finance/balance.py
───────────────────────────────────
Public-facing DTOs for student financial balances.
View-based balance tracking - no materialized tables.
"""
from typing import Optional

from pydantic import BaseModel


class UnpaidEnrollmentItem(BaseModel):
    """Single item for unpaid enrollment listing from v_unpaid_enrollments."""
    enrollment_id: int
    student_id: int
    student_name: str
    group_id: int
    group_name: str
    course_name: Optional[str]
    level_number: int
    amount_due: float
    discount_applied: float
    total_paid: float
    remaining_balance: float
    enrolled_at: Optional[str]


class EnrollmentBalanceResponse(BaseModel):
    """Response schema for enrollment balance from v_enrollment_balance."""
    enrollment_id: int
    student_id: int
    group_id: int
    level_number: int
    amount_due: float
    discount_applied: float
    total_paid: float
    total_refunded: float
    remaining_balance: float
    status: str
    is_paid: bool

    model_config = {"from_attributes": True}
