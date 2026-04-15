"""
app/modules/finance/interfaces/dto/receipt_finalized_dto.py
─────────────────────────────────────────────────────────────
Receipt finalized DTO.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List

from app.modules.finance.interfaces.dto.receipt_line_item_dto import ReceiptLineItemDTO


@dataclass(frozen=True)
class ReceiptFinalizedDTO:
    """Immutable DTO for finalized receipt response."""
    receipt_id: int
    receipt_number: str
    payment_method: str
    paid_at: datetime
    lines: List[ReceiptLineItemDTO]
    total: Decimal
    payment_ids: List[int]
