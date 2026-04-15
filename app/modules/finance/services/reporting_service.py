"""
app/modules/finance/services/reporting_service.py
──────────────────────────────────────────────
Reporting service implementation for financial reports.
"""
from datetime import date
from typing import Optional, List

from app.modules.finance.interfaces import IReportingService
from app.modules.finance import DailyCollectionItem, DailyReceiptItem, UnpaidCompFeeItem
from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork


class ReportingService(IReportingService):
    """
    Service for financial reporting operations.
    
    Responsible for:
    - Daily collection summaries
    - Daily receipt listings
    - Unpaid competition fees reports
    """

    def __init__(self, uow: FinanceUnitOfWork) -> None:
        self._uow = uow

    def get_daily_collections(
        self, target_date: Optional[date] = None
    ) -> List[DailyCollectionItem]:
        """Get daily collection summary by payment method."""
        if target_date is None:
            target_date = date.today()

        return self._uow.reporting.get_daily_collections(target_date)

    def get_daily_receipts(
        self, target_date: Optional[date] = None
    ) -> List[DailyReceiptItem]:
        """Get all receipts issued on a specific date."""
        if target_date is None:
            target_date = date.today()

        return self._uow.receipts.list_by_date(target_date)

    def get_unpaid_competition_fees(
        self, student_id: int
    ) -> List[UnpaidCompFeeItem]:
        """Get unpaid competition fee records for a student."""
        return self._uow.reporting.get_unpaid_competition_fees(student_id)
