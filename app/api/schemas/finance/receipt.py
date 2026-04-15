"""
app/api/schemas/finance/receipt.py
────────────────────────────────────
Public-facing Receipt DTOs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.modules.finance import ReceiptLineInput


class ReceiptCreatedPublic(BaseModel):
    """
    Response returned when a new receipt is created.
    """
    receipt_id: int
    receipt_number: Optional[str] = None
    payment_method: str
    paid_at: Optional[datetime] = None
    lines: int
    total: float
    payment_ids: list[int]


class ReceiptLinePublic(BaseModel):
    id: int
    student_id: int
    enrollment_id: Optional[int] = None
    amount: float
    transaction_type: str
    payment_type: str
    discount: float = 0.0
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ReceiptHeaderPublic(BaseModel):
    id: int
    receipt_number: Optional[str] = None
    payer_name: Optional[str] = None
    payment_method: str
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ReceiptDetailPublic(BaseModel):
    """
    Full detail including lines.
    """
    receipt: ReceiptHeaderPublic
    lines: list[ReceiptLinePublic]
    total: float


class ReceiptListItem(BaseModel):
    """
    Slim receipt for search endpoints.
    """
    id: int
    receipt_number: Optional[str] = None
    payer_name: Optional[str] = None
    payment_method: str
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RefundResultPublic(BaseModel):
    """
    Result of issuing a refund.
    """
    receipt_number: Optional[str] = None
    refunded_amount: float
    new_balance: Optional[float] = None


class CreateReceiptRequest(BaseModel):
    payer_name: Optional[str] = None
    method: str = "cash"
    notes: Optional[str] = None
    allow_credit: bool = True
    lines: list[ReceiptLineInput]


class IssueRefundRequest(BaseModel):
    payment_id: int
    amount: float
    reason: str
    method: str = "cash"
