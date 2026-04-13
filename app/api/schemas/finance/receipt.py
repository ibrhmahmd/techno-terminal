"""
app/api/schemas/finance/receipt.py
────────────────────────────────────
Public-facing Receipt DTOs.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


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


class ReceiptLineRequest(BaseModel):
    """Input for creating a receipt line (ID assigned by database)."""
    student_id: int
    enrollment_id: Optional[int] = None
    amount: float
    payment_type: str = "course_level"
    discount: float = 0.0
    notes: Optional[str] = None


class CreateReceiptRequest(BaseModel):
    payer_name: Optional[str] = None
    method: str = "cash"
    notes: Optional[str] = None
    allow_credit: bool = True
    lines: list[ReceiptLineRequest]


class IssueRefundRequest(BaseModel):
    payment_id: int
    amount: float
    reason: str
    method: str = "cash"


class GenerateReceiptRequest(BaseModel):
    """Request schema for receipt generation."""
    template_name: str = "standard"
    include_balance: bool = True


class MarkReceiptSentRequest(BaseModel):
    """Request to mark a receipt as sent to parent."""
    parent_email: Optional[str] = None


class BatchGenerateRequest(BaseModel):
    """Request to generate multiple receipts in batch."""
    receipt_ids: list[int]
    template_name: str = "standard"


class ReceiptGeneratedDTO(BaseModel):
    """Structured response for receipt generation with content and metadata."""
    receipt_id: int
    content: str
    template_name: str
    include_balance: bool
    generated_at: datetime
    content_type: str = "text/plain"


class BatchReceiptResultDTO(BaseModel):
    """Result item for batch receipt generation with explicit success/error tracking."""
    receipt_id: int
    success: bool
    content: Optional[str] = None  # Populated if success=True
    error_message: Optional[str] = None  # Populated if success=False
    error_code: Optional[str] = None  # 'not_found', 'generation_failed', 'invalid_template', etc.


class BatchGenerateResponse(BaseModel):
    """Response item for batch receipt generation (legacy, use BatchReceiptResultDTO)."""
    receipt_id: int
    content: str  # Either receipt text or error message


class ReceiptFinalizedDTO(BaseModel):
    """Result of finalizing a receipt with charge lines.
    
    This provides a typed structure for the receipt finalization response,
    ensuring all required fields are present and properly typed.
    """
    receipt_id: int
    receipt_number: str
    payment_method: str
    paid_at: datetime
    lines: list[ReceiptLinePublic]
    total: float
    payment_ids: list[int]

    model_config = {"from_attributes": True}
