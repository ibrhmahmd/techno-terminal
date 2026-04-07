"""
app/api/schemas/finance/balance.py
───────────────────────────────────
Public-facing DTOs for student financial balances.
"""
from typing import Optional

from pydantic import BaseModel


class FinancialSummaryPublic(BaseModel):
    """
    Financial summary per enrollment returned from v_enrollment_balance.
    """
    student_id: int
    group_id: int
    enrollment_id: int
    group_name: Optional[str] = None
    net_due: float
    total_paid: float
    balance: float

    model_config = {"from_attributes": True}
