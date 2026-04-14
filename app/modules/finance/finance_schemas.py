"""
app/modules/finance/finance_schemas.py
────────────────────────────────────────
Typed input DTOs for the Finance service layer.
"""
from datetime import date, datetime
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


class UnpaidCompFeeItem(BaseModel):
    """
    Output DTO for unpaid competition fee records.
    Used by Financial Desk to render checkbox payment lines.
    """
    team_member_id: int      # FK to mark fee paid
    team_id: int
    team_name: str
    competition_name: str
    category_name: str
    member_share: float      # Snapshotted amount at registration
    student_id: int

    model_config = {"from_attributes": True}


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


class DailyCollectionItem(BaseModel):
    """Daily collection summary by payment method."""
    payment_method: str
    total_amount: float
    receipt_count: int
    target_date: date

    model_config = {"from_attributes": True}


class DailyReceiptItem(BaseModel):
    """Receipt summary for daily reporting."""
    receipt_id: int
    receipt_number: str
    payer_name: Optional[str]
    total_amount: float
    payment_method: str
    issued_at: datetime

    model_config = {"from_attributes": True}


class ReceiptSearchItem(BaseModel):
    """Receipt search result item."""
    id: int
    receipt_number: Optional[str]
    payer_name: Optional[str]
    payment_method: str
    paid_at: datetime

    model_config = {"from_attributes": True}
