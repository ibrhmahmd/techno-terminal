"""
app/modules/finance/services/reporting_service.py
──────────────────────────────────────────────
Reporting service implementation for financial reports.
"""
from datetime import date
from typing import Optional, List

from app.modules.finance.schemas import DailyCollectionItem, DailyReceiptItem, UnpaidCompFeeItem
from app.db.uow import UnitOfWork
from app.modules.finance.repositories.receipt_repository import ReceiptRepository
from app.modules.finance.repositories.reporting_repository import ReportingRepository


class ReportingService:
    """
    Service for financial reporting operations.
    
    Responsible for:
    - Daily collection summaries
    - Daily receipt listings
    - Unpaid competition fees reports
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._receipts = ReceiptRepository(uow.session)
        self._reporting = ReportingRepository(uow.session)

    def get_daily_collections(
        self, target_date: Optional[date] = None
    ) -> List[DailyCollectionItem]:
        """Get daily collection summary by payment method."""
        if target_date is None:
            target_date = date.today()

        return self._reporting.get_daily_collections(target_date)

    def get_daily_receipts(
        self, target_date: Optional[date] = None
    ) -> List[DailyReceiptItem]:
        """Get all receipts issued on a specific date."""
        if target_date is None:
            target_date = date.today()

        return self._receipts.list_by_date(target_date)

    def get_unpaid_competition_fees(
        self, student_id: int
    ) -> List[UnpaidCompFeeItem]:
        """Get unpaid competition fee records for a student."""
        return self._reporting.get_unpaid_competition_fees(student_id)
