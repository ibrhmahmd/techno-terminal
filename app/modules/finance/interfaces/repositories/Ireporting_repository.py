"""
Reporting repository protocol.
"""
from datetime import date
from typing import List, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.schemas import (
        DailyCollectionItem,
        UnpaidCompFeeItem,
    )


@runtime_checkable
class IReportingRepository(Protocol):
    """Protocol for reporting and analytics data access."""

    def get_daily_collections(
        self, target_date: date
    ) -> List["DailyCollectionItem"]: ...

    def get_unpaid_competition_fees(
        self, student_id: int
    ) -> List["UnpaidCompFeeItem"]: ...
