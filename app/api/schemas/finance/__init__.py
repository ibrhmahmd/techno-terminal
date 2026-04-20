"""
app/api/schemas/finance/__init__.py

Finance API DTOs - All exports use standardized naming:
- Request: Input DTOs for POST/PUT endpoints
- Response: Output DTOs for all endpoints  
- Item: List item DTOs
"""
from .receipt import (
    ReceiptCreationResponse,
    ReceiptDetailResponse,
    ReceiptListItem,
    RefundResponse,
    CreateReceiptRequest,
    IssueRefundRequest,
    ReceiptLineRequest,
    MarkReceiptSentRequest,
    BatchGenerateRequest,
    BatchReceiptItem,
    ReceiptGenerationResponse,
    BatchGenerateResponse,
)
from .balance import (
    UnpaidEnrollmentItem,
    EnrollmentBalanceResponse,
    StudentBalanceResponse,
)
from .risk import (
    PreviewOverpaymentRequest,
    OverpaymentRiskResponse,
)

__all__ = [
    # Receipt
    "ReceiptCreationResponse",
    "ReceiptDetailResponse",
    "ReceiptListItem",
    "RefundResponse",
    "CreateReceiptRequest",
    "IssueRefundRequest",
    "ReceiptLineRequest",
    "MarkReceiptSentRequest",
    "BatchGenerateRequest",
    "BatchReceiptItem",
    "ReceiptGenerationResponse",
    "BatchGenerateResponse",
    # Balance (view-based)
    "UnpaidEnrollmentItem",
    "EnrollmentBalanceResponse",
    "StudentBalanceResponse",
    # Risk
    "PreviewOverpaymentRequest",
    "OverpaymentRiskResponse",
]
