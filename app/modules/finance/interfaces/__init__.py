"""
app/modules/finance/interfaces/__init__.py
─────────────────────────────────────────
Abstract interfaces for the Finance module.

Granular organization - each protocol in its own file.
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
    # Payment DTOs
    EnrollmentBalanceDTO,
    AddPaymentLineDTO,
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

# Repository Protocols
from app.modules.finance.interfaces.repositories import (
    IReceiptRepository,
    IPaymentRepository,
    IReportingRepository,
)

# Service Protocols
from app.modules.finance.interfaces.services import (
    IReceiptService,
    IRefundService,
    IBalanceService,
    IReportingService,
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
    "EnrollmentBalanceDTO",
    "AddPaymentLineDTO",
    "RefundResultDTO",
    "IssueRefundDTO",
    "OverpaymentRiskItem",
    "StudentBalanceSummaryDTO",
    "PaginatedEnrollmentBalancesDTO",
    "ReceiptTemplateContextDTO",
    # Repository Protocols
    "IReceiptRepository",
    "IPaymentRepository",
    "IReportingRepository",
    # Service Protocols
    "IReceiptService",
    "IRefundService",
    "IBalanceService",
    "IReportingService",
]
