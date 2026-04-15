"""
Reporting service protocol.
"""
from datetime import date
from typing import List, Optional, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.schemas import (
        DailyCollectionItem,
        DailyReceiptItem,
        UnpaidCompFeeItem,
    )


@runtime_checkable
class IReportingService(Protocol):
    """Protocol for financial reporting operations."""

    def get_daily_collections(
        self, target_date: Optional[date] = None
    ) -> List["DailyCollectionItem"]: ...

    def get_daily_receipts(
        self, target_date: Optional[date] = None
    ) -> List["DailyReceiptItem"]: ...

    def get_unpaid_competition_fees(
        self, student_id: int
    ) -> List["UnpaidCompFeeItem"]: ...
