"""
app/modules/finance/interfaces/__init__.py
─────────────────────────────────────────
Internal DTOs for the Finance module.

Granular organization - each DTO in its own file.
"""

# DTOs (organized by domain)
from app.modules.finance.interfaces.dto import (
    # Receipt DTOs
    ReceiptWithLinesDTO,
    ReceiptLineItemDTO,
    ReceiptFinalizedDTO,
    ReceiptDetailDTO,
    CreateReceiptDTO,
    SearchReceiptsDTO,
    CreateReceiptServiceDTO,
    EnhancedReceiptLineDTO,
    # Payment DTOs
    EnrollmentBalanceDTO,
    AddPaymentLineDTO,
    PaymentWithDetailsDTO,
    PaymentListItemDTO,
    PaginatedStudentPaymentsDTO,
    SendReceiptResultDTO,
    # Refund DTOs
    RefundResultDTO,
    IssueRefundDTO,
    # Balance DTOs
    OverpaymentRiskItem,
    StudentBalanceSummaryDTO,
    PaginatedEnrollmentBalancesDTO,
    # Reporting DTOs
    ReceiptTemplateContextDTO,
)

__all__ = [
    # DTOs
    "ReceiptWithLinesDTO",
    "ReceiptLineItemDTO",
    "ReceiptFinalizedDTO",
    "ReceiptDetailDTO",
    "CreateReceiptDTO",
    "SearchReceiptsDTO",
    "CreateReceiptServiceDTO",
    "EnhancedReceiptLineDTO",
    "EnrollmentBalanceDTO",
    "AddPaymentLineDTO",
    "PaymentWithDetailsDTO",
    "PaymentListItemDTO",
    "PaginatedStudentPaymentsDTO",
    "SendReceiptResultDTO",
    "RefundResultDTO",
    "IssueRefundDTO",
    "OverpaymentRiskItem",
    "StudentBalanceSummaryDTO",
    "PaginatedEnrollmentBalancesDTO",
    "ReceiptTemplateContextDTO",
]
