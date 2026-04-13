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
    StudentBalanceResponse,
    UnpaidEnrollmentItem,
    EnrollmentBalanceResponse,
    BalanceAdjustmentRequest,
    BalanceAdjustmentResponse,
    BalanceSummaryResponse,
)
from .allocations import (
    AllocationReversalResponse,
    PaymentAllocationItem,
    PaymentAllocationsResponse,
)
from .credit import (
    CreditApplicationItem,
    ApplyCreditRequest,
    ApplyCreditResponse,
    CreditBalanceResponse,
    StudentCreditInfo,
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
    # Balance
    "StudentBalanceResponse",
    "UnpaidEnrollmentItem",
    "EnrollmentBalanceResponse",
    "BalanceAdjustmentRequest",
    "BalanceAdjustmentResponse",
    "BalanceSummaryResponse",
    # Allocations
    "AllocationReversalResponse",
    "PaymentAllocationItem",
    "PaymentAllocationsResponse",
    # Credit
    "CreditApplicationItem",
    "ApplyCreditRequest",
    "ApplyCreditResponse",
    "CreditBalanceResponse",
    "StudentCreditInfo",
    # Risk
    "PreviewOverpaymentRequest",
    "OverpaymentRiskResponse",
]
