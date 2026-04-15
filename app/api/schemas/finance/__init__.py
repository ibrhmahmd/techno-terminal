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
    ReceiptGenerationResponse,
    BatchReceiptItem,
    CreateReceiptRequest,
    IssueRefundRequest,
    MarkReceiptSentRequest,
    BatchGenerateRequest,
    ReceiptLineRequest,
)
from .balance import (
    UnpaidEnrollmentItem,
    EnrollmentBalanceResponse,
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
    "ReceiptGenerationResponse",
    "BatchReceiptItem",
    "CreateReceiptRequest",
    "IssueRefundRequest",
    "MarkReceiptSentRequest",
    "BatchGenerateRequest",
    "ReceiptLineRequest",
    # Balance (view-based)
    "UnpaidEnrollmentItem",
    "EnrollmentBalanceResponse",
    # Risk
    "PreviewOverpaymentRequest",
    "OverpaymentRiskResponse",
]
