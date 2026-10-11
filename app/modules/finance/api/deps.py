"""Finance HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.deps import UoW
from app.modules.crm import StudentActivityService
from app.modules.finance.ports import PaymentNotifier
from app.modules.finance.services.balance_service import BalanceService
from app.modules.finance.services.competition_fee_service import CompetitionFeeService
from app.modules.finance.services.receipt_generation_service import ReceiptGenerationService
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.finance.services.refund_service import RefundService
from app.modules.finance.services.reporting_service import ReportingService
from app.modules.finance.services.student_payment_service import StudentPaymentService


def get_payment_notifier() -> PaymentNotifier:
    """PaymentNotifier provider — overridden in create_app() with the real adapter."""
    raise NotImplementedError("wired in create_app()")


def get_student_payment_service(
    uow: UoW,
    notifier: PaymentNotifier = Depends(get_payment_notifier),
) -> StudentPaymentService:
    return StudentPaymentService(uow, notifier=notifier)


def get_receipt_service(
    uow: UoW,
    notifier: PaymentNotifier = Depends(get_payment_notifier),
) -> ReceiptService:
    """Returns a ReceiptService with activity logging and the notifier port."""
    return ReceiptService(uow, activity_svc=StudentActivityService(uow), notifier=notifier)


def get_refund_service(uow: UoW) -> RefundService:
    """Returns a RefundService with activity logging."""
    return RefundService(uow, activity_svc=StudentActivityService(uow))


def get_balance_service(uow: UoW) -> BalanceService:
    return BalanceService(uow)


def get_reporting_service(uow: UoW) -> ReportingService:
    return ReportingService(uow)


def get_competition_fee_service(
    uow: UoW,
    notifier: PaymentNotifier = Depends(get_payment_notifier),
) -> CompetitionFeeService:
    return CompetitionFeeService(uow, notifier=notifier)


def get_receipt_generation_service(uow: UoW) -> ReceiptGenerationService:
    return ReceiptGenerationService(uow)
