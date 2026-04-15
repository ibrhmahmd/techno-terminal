"""
app/modules/finance/interfaces/dto/receipt_detail_dto.py
───────────────────────────────────────────────────────────
Receipt detail DTO.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, List

from app.modules.finance.interfaces.dto.receipt_line_item_dto import ReceiptLineItemDTO

if TYPE_CHECKING:
    from app.modules.finance.models import Receipt


@dataclass(frozen=True)
class ReceiptDetailDTO:
    """Immutable DTO for detailed receipt response."""
    receipt: "Receipt"
    lines: List[ReceiptLineItemDTO]
    total: Decimal
