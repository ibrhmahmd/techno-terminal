"""
app/modules/finance/repositories/unit_of_work.py
──────────────────────────────────────────────
Unit of Work pattern for transaction management.

Ensures atomic operations across multiple repositories.
"""
from typing import Optional

from sqlmodel import Session

from app.db.connection import get_session
from app.modules.finance.repositories.receipt_repository import ReceiptRepository
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.modules.finance.repositories.reporting_repository import ReportingRepository


class FinanceUnitOfWork:
    """
    Unit of Work for finance operations.
    
    Manages a single database session and provides access to
    all finance repositories. Ensures atomic commits/rollbacks.
    
    Usage:
        with FinanceUnitOfWork() as uow:
            receipt = uow.receipts.create(...)
            payment = uow.payments.add_line(...)
            uow.commit()
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._own_session = session is None
        self._receipts: Optional[ReceiptRepository] = None
        self._payments: Optional[PaymentRepository] = None
        self._reporting: Optional[ReportingRepository] = None

    def __enter__(self) -> "FinanceUnitOfWork":
        if self._own_session:
            self._session_cm = get_session()
            self._session = self._session_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        
        if self._own_session:
            self._session_cm.__exit__(exc_type, exc_val, exc_tb)

    @property
    def receipts(self) -> ReceiptRepository:
        if self._receipts is None:
            self._receipts = ReceiptRepository(self._session)
        return self._receipts

    @property
    def payments(self) -> PaymentRepository:
        if self._payments is None:
            self._payments = PaymentRepository(self._session)
        return self._payments

    @property
    def reporting(self) -> ReportingRepository:
        if self._reporting is None:
            self._reporting = ReportingRepository(self._session)
        return self._reporting

    def commit(self) -> None:
        """Commit the current transaction."""
        self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._session.rollback()

    def flush(self) -> None:
        """Flush pending changes to database without committing."""
        self._session.flush()
