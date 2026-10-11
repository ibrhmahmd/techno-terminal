"""
app/modules/finance/__init__.py
───────────────────────────────
Finance Module Facade (ADR-0003)

Other modules must import Finance ONLY via this facade, except
app.modules.finance.models which anyone may import (ADR-0004).

Exports:
- Models: Receipt, Payment
- Services: ReceiptService, RefundService, BalanceService, ReportingService,
            StudentPaymentService
- Ports: PaymentNotifier
- DTOs: ReceiptLineInput, CreateReceiptServiceDTO, IssueRefundDTO,
        RefundResultDTO, SearchReceiptsDTO, ReceiptDetailDTO, ReceiptSearchItem,
        UnpaidCompFeeItem, DailyCollectionItem, DailyReceiptItem
- PDF: build_receipt_pdf

(CompetitionFeeService stays reachable at
app.modules.finance.services.competition_fee_service: it imports the competitions
facade, and exporting it here would create an import cycle through
competitions' model registration.)
"""

from .models import Receipt, Payment
from .ports import PaymentNotifier
from .schemas import (
    CreateReceiptServiceDTO,
    DailyCollectionItem,
    DailyReceiptItem,
    IssueRefundDTO,
    ReceiptDetailDTO,
    ReceiptLineInput,
    ReceiptSearchItem,
    RefundResultDTO,
    SearchReceiptsDTO,
    UnpaidCompFeeItem,
)
from .services.balance_service import BalanceService
from .services.receipt_service import ReceiptService
from .services.refund_service import RefundService
from .services.reporting_service import ReportingService
from .services.student_payment_service import StudentPaymentService
from .pdf.receipt_pdf import build_receipt_pdf

__all__ = [
    "Receipt",
    "Payment",
    "PaymentNotifier",
    "ReceiptService",
    "RefundService",
    "BalanceService",
    "ReportingService",
    "StudentPaymentService",
    "ReceiptLineInput",
    "CreateReceiptServiceDTO",
    "IssueRefundDTO",
    "RefundResultDTO",
    "SearchReceiptsDTO",
    "ReceiptDetailDTO",
    "ReceiptSearchItem",
    "UnpaidCompFeeItem",
    "DailyCollectionItem",
    "DailyReceiptItem",
    "build_receipt_pdf",
]
