"""
Receipt service protocol.
"""
from typing import List, Optional, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.interfaces.dto import (
        ReceiptDetailDTO,
        ReceiptFinalizedDTO,
        CreateReceiptServiceDTO,
        SearchReceiptsDTO,
    )
    from app.modules.finance.schemas import ReceiptSearchItem


@runtime_checkable
class IReceiptService(Protocol):
    """Protocol for receipt business operations."""

    def create(self, dto: "CreateReceiptServiceDTO") -> "ReceiptFinalizedDTO": ...

    def get_detail(self, receipt_id: int) -> Optional["ReceiptDetailDTO"]: ...

    def search(self, criteria: "SearchReceiptsDTO") -> List["ReceiptSearchItem"]: ...

    def generate_pdf(self, receipt_id: int) -> bytes: ...

    def mark_as_sent(self, receipt_id: int) -> None: ...
