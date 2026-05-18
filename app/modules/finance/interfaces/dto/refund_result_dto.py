"""
app/modules/finance/interfaces/dto/refund_result_dto.py
─────────────────────────────────────────────────────────
Refund result DTO.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class RefundResultDTO:
    """Immutable DTO for refund operation result."""
    receipt_number: str
    refunded_amount: Decimal
    new_balance: Optional[Decimal] = None
