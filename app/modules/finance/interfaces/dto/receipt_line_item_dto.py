"""
app/modules/finance/interfaces/dto/receipt_line_item_dto.py
──────────────────────────────────────────────────────────────
Receipt line item DTO.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ReceiptLineItemDTO:
    """Immutable DTO for a receipt line in responses."""
    id: int
    student_id: int
    enrollment_id: Optional[int]
    amount: Decimal
    transaction_type: str
    payment_type: Optional[str]
