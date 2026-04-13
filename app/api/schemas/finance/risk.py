"""
app/api/schemas/finance/risk.py
──────────────────────────────
Risk assessment schemas for finance operations.

Defines request/response models for overpayment risk preview and related
financial risk calculations, strictly separated from router logic.
"""
from pydantic import BaseModel

from app.api.schemas.finance.receipt import ReceiptLineRequest


class PreviewOverpaymentRequest(BaseModel):
    """Request to preview overpayment risk for receipt lines."""
    lines: list[ReceiptLineRequest]


class OverpaymentRiskResponse(BaseModel):
    """Response showing potential credit/overpayment for a line item."""
    student_id: int
    enrollment_id: int
    amount: float
    debt_before: float
    projected_balance: float
    excess_credit: float

    model_config = {"from_attributes": True}
