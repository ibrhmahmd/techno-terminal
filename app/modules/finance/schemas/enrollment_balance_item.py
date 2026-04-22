"""
app/modules/finance/schemas/enrollment_balance_item.py
────────────────────────────────────────────────────────
Enrollment balance item schema.
"""
from typing import Optional

from pydantic import BaseModel


class EnrollmentBalanceItem(BaseModel):
    """Balance details for a single enrollment (from v_unpaid_enrollments)."""

    enrollment_id: int
    student_id: int
    student_name: str
    group_id: int
    group_name: str
    course_name: Optional[str]
    level_number: int
    amount_due: float
    discount_applied: float
    amount_paid: float
    remaining_balance: float
    status: str  # 'paid', 'partial', 'unpaid'
    enrolled_at: Optional[str]

    model_config = {"from_attributes": True}
