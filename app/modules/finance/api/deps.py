"""Finance HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends
from sqlmodel import Session

from app.api.dependencies import get_db, get_notification_service
from app.db.uow import UnitOfWork
from app.modules.crm import StudentActivityService
from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
from app.modules.finance.services.balance_service import BalanceService
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.finance.services.refund_service import RefundService
from app.modules.finance.services.reporting_service import ReportingService
from app.modules.finance.services.student_payment_service import StudentPaymentService


def get_student_payment_service(
    session: Session = Depends(get_db),
) -> StudentPaymentService:
    """Returns a StudentPaymentService with a fresh UnitOfWork."""
    uow = FinanceUnitOfWork(session=session)
    return StudentPaymentService(uow)


def get_receipt_service(
    session: Session = Depends(get_db),
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> ReceiptService:
    """Returns a ReceiptService with activity logging and notifications."""
    finance_uow = FinanceUnitOfWork(session=session)
    crm_uow = UnitOfWork(session)
    activity_svc = StudentActivityService(crm_uow)
    return ReceiptService(
        finance_uow,
        activity_svc=activity_svc,
        notification_svc=notification_svc,
    )


def get_refund_service(
    session: Session = Depends(get_db),
) -> RefundService:
    """Returns a RefundService with activity logging."""
    finance_uow = FinanceUnitOfWork(session=session)
    crm_uow = UnitOfWork(session)
    activity_svc = StudentActivityService(crm_uow)
    return RefundService(finance_uow, activity_svc=activity_svc)


def get_balance_service(
    session: Session = Depends(get_db),
) -> BalanceService:
    """Returns a BalanceService with a fresh UnitOfWork."""
    uow = FinanceUnitOfWork(session=session)
    return BalanceService(uow)


def get_reporting_service(
    session: Session = Depends(get_db),
) -> ReportingService:
    """Returns a ReportingService with a fresh UnitOfWork."""
    uow = FinanceUnitOfWork(session=session)
    return ReportingService(uow)
