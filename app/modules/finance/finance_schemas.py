"""
app/modules/finance/finance_schemas.py
────────────────────────────────────────
Typed input DTOs for the Finance service layer.
"""
from typing import Optional
from pydantic import BaseModel, field_validator
from app.shared.constants import PaymentMethod
from app.shared.validators import validate_positive_amount


class ReceiptLineInput(BaseModel):
    """One charge line for create_receipt_with_charge_lines (no receipt_id yet)."""

    student_id: int
    enrollment_id: Optional[int] = None
    team_member_id: Optional[int] = None   # Set for competition payments — links to TeamMember
    amount: float
    payment_type: str = "course_level"
    discount: float = 0.0
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        validate_positive_amount(v, field="amount")
        return v


class OpenReceiptInput(BaseModel):
    """Input for finance_service.open_receipt()."""
    payer_name: Optional[str] = None
    method: PaymentMethod | str = "cash"
    received_by_user_id: Optional[int] = None
    notes: Optional[str] = None


class AddChargeLineInput(BaseModel):
    """Input for finance_service.add_charge_line()."""
    receipt_id: int
    student_id: int
    enrollment_id: Optional[int] = None
    amount: float
    payment_type: str = "course_level"
    discount: float = 0.0
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        validate_positive_amount(v, field="amount")
        return v


class IssueRefundInput(BaseModel):
    """Input for finance_service.issue_refund()."""
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
