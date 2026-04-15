"""
app/modules/finance/interfaces/dto/receipt_with_lines_dto.py
─────────────────────────────────────────────────────────────
Receipt with lines DTO.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from app.modules.finance.models import Receipt, Payment


@dataclass(frozen=True)
class ReceiptWithLinesDTO:
    """Immutable DTO for receipt with its payment lines."""
    receipt: "Receipt"
    lines: List["Payment"]
