"""
app/modules/finance/schemas/enrollment_balance_item.py
────────────────────────────────────────────────────────
Enrollment balance item schema.
"""
from pydantic import BaseModel


class EnrollmentBalanceItem(BaseModel):
    """Balance details for a single enrollment (from v_enrollment_balance)."""

    enrollment_id: int
    student_id: int
    group_id: int
    level_number: int
    amount_due: float
    discount_applied: float
    amount_paid: float
    remaining_balance: float
    status: str  # 'paid', 'partial', 'unpaid'

    model_config = {"from_attributes": True}
