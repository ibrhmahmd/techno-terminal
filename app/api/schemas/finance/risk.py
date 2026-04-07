"""
app/api/schemas/finance/risk.py
──────────────────────────────
Risk assessment schemas for finance operations.

Defines request/response models for overpayment risk preview and related
financial risk calculations, strictly separated from router logic.
"""
from pydantic import BaseModel

from app.modules.finance.finance_schemas import ReceiptLineInput


class PreviewRiskRequest(BaseModel):
    """Request to preview overpayment risk for receipt lines."""
    lines: list[ReceiptLineInput]


class OverpaymentRiskItem(BaseModel):
    """Risk item showing potential credit/overpayment."""
    student_id: int
    enrollment_id: int
    amount: float
    debt_before: float
    projected_balance: float
    excess_credit: float

    model_config = {"from_attributes": True}
