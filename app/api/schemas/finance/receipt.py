"""
app/api/schemas/finance/receipt.py
────────────────────────────────────
Public-facing Receipt DTOs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.modules.finance import ReceiptLineInput


class ReceiptCreationResponse(BaseModel):
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


class ReceiptLineResponse(BaseModel):
    id: int
    student_id: int
    enrollment_id: Optional[int] = None
    amount: float
    transaction_type: str
    payment_type: str
    discount: float = 0.0
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ReceiptHeaderResponse(BaseModel):
    id: int
    receipt_number: Optional[str] = None
    payer_name: Optional[str] = None
    payment_method: str
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ReceiptDetailResponse(BaseModel):
    """
    Full detail including lines.
    """
    receipt: ReceiptHeaderResponse
    lines: list[ReceiptLineResponse]
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


class RefundResponse(BaseModel):
    """
    Result of issuing a refund.
    """
    receipt_number: Optional[str] = None
    refunded_amount: float
    new_balance: Optional[float] = None


class ReceiptLineRequest(BaseModel):
    """Line item for receipt creation requests."""
    student_id: int
    enrollment_id: Optional[int] = None
    amount: float
    payment_type: str = "course_level"


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


class BatchReceiptItem(BaseModel):
    """Item in batch receipt generation response."""
    receipt_id: int
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class MarkReceiptSentRequest(BaseModel):
    """Request to mark a receipt as sent."""
    pass


class BatchGenerateRequest(BaseModel):
    """Request for batch receipt generation."""
    receipt_ids: list[int]
    template_name: str = "standard"


class ReceiptGenerationResponse(BaseModel):
    """Response for single receipt generation."""
    content: str
    content_type: str = "text/plain"


class BatchGenerateResponse(BaseModel):
    """Response for batch receipt generation."""
    items: list[BatchReceiptItem]
    total_count: int
    success_count: int
    failed_count: int

