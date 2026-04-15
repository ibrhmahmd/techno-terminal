"""
Receipt repository protocol.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.models import Receipt
    from app.modules.finance.interfaces.dto import (
        ReceiptWithLinesDTO,
        CreateReceiptDTO,
        SearchReceiptsDTO,
    )
    from app.modules.finance.schemas import DailyReceiptItem, ReceiptSearchItem


@runtime_checkable
class IReceiptRepository(Protocol):
    """Protocol for receipt data access operations."""

    def create(self, dto: "CreateReceiptDTO") -> "Receipt": ...

    def set_receipt_number(self, receipt_id: int) -> None: ...

    def get_by_id(self, receipt_id: int) -> Optional["Receipt"]: ...

    def get_with_lines(
        self, receipt_id: int
    ) -> Optional["ReceiptWithLinesDTO"]: ...

    def get_total(self, receipt_id: int) -> Decimal: ...

    def list_by_date(
        self, target_date: date, limit: int = 1000
    ) -> List["DailyReceiptItem"]: ...

    def search(self, criteria: "SearchReceiptsDTO") -> List["ReceiptSearchItem"]: ...
