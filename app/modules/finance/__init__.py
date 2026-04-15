"""
app/modules/finance/__init__.py
──────────────────────────────
Finance module with SOLID-compliant architecture.

New Structure:
- models: SQLModel database models (single-responsibility files)
- schemas: Pydantic input/output DTOs (organized by domain)
- interfaces: Protocols and internal DTOs
- repositories: Data access layer with UnitOfWork
- services: Business logic layer
- pdf: PDF generation utilities
"""

# Domain models
from .models import Receipt, Payment

# Schemas/DTOs
from .schemas import (
    ReceiptLineInput,
    IssueRefundInput,
    EnrollmentBalanceItem,
    DailyCollectionItem,
    DailyReceiptItem,
    ReceiptSearchItem,
    UnpaidCompFeeItem,
)

# Services (SOLID-compliant)
from .services.receipt_service import ReceiptService
from .services.refund_service import RefundService
from .services.balance_service import BalanceService
from .services.reporting_service import ReportingService

# Repositories
from .repositories.unit_of_work import FinanceUnitOfWork
from .repositories.receipt_repository import ReceiptRepository
from .repositories.payment_repository import PaymentRepository
from .repositories.reporting_repository import ReportingRepository

# PDF generation
from .pdf.receipt_pdf import build_receipt_pdf, ReceiptPDF

# Interface DTOs (for parameter wrapping and internal communication)
from .interfaces.dto import (
    ReceiptWithLinesDTO,
    ReceiptLineItemDTO,
    ReceiptDetailDTO,
    CreateReceiptDTO,
    SearchReceiptsDTO,
    CreateReceiptServiceDTO,
    EnrollmentBalanceDTO,
    AddPaymentLineDTO,
    RefundResultDTO,
    IssueRefundDTO,
    OverpaymentRiskItem,
    ReceiptTemplateContextDTO,
)

# Protocols
from .interfaces.repositories import (
    IReceiptRepository,
    IPaymentRepository,
    IReportingRepository,
)
from .interfaces.services import (
    IReceiptService,
    IRefundService,
    IBalanceService,
    IReportingService,
)

__all__ = [
    # Models
    "Receipt",
    "Payment",
    # Schemas
    "ReceiptLineInput",
    "IssueRefundInput",
    "EnrollmentBalanceItem",
    "DailyCollectionItem",
    "DailyReceiptItem",
    "ReceiptSearchItem",
    "UnpaidCompFeeItem",
    # Services
    "ReceiptService",
    "RefundService",
    "BalanceService",
    "ReportingService",
    # Repositories
    "FinanceUnitOfWork",
    "ReceiptRepository",
    "PaymentRepository",
    "ReportingRepository",
    # PDF
    "build_receipt_pdf",
    "ReceiptPDF",
    # Interface DTOs
    "ReceiptWithLinesDTO",
    "ReceiptLineItemDTO",
    "ReceiptDetailDTO",
    "CreateReceiptDTO",
    "SearchReceiptsDTO",
    "CreateReceiptServiceDTO",
    "EnrollmentBalanceDTO",
    "AddPaymentLineDTO",
    "RefundResultDTO",
    "IssueRefundDTO",
    "OverpaymentRiskItem",
    "ReceiptTemplateContextDTO",
    # Protocols
    "IReceiptRepository",
    "IPaymentRepository",
    "IReportingRepository",
    "IReceiptService",
    "IRefundService",
    "IBalanceService",
    "IReportingService",
]
