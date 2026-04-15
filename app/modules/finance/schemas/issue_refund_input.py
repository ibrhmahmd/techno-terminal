"""
app/modules/finance/schemas/issue_refund_input.py
─────────────────────────────────────────────────
Issue refund input schema.
"""
from typing import Optional
from pydantic import BaseModel, field_validator
from app.shared.constants import PaymentMethod
from app.shared.validators import validate_positive_amount


class IssueRefundInput(BaseModel):
    """Input for issuing a refund."""

    payment_id: int
    amount: float
    reason: str
    received_by_user_id: Optional[int] = None
    method: PaymentMethod | str = "cash"

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        validate_positive_amount(v, field="refund amount")
        return v
