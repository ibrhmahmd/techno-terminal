"""
app/modules/finance/interfaces/dto/add_payment_line_dto.py
──────────────────────────────────────────────────────────────
Add payment line DTO.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class AddPaymentLineDTO:
    """Parameters for adding a payment line."""
    receipt_id: int
    student_id: int
    enrollment_id: Optional[int]
    amount: Decimal
    transaction_type: str
    payment_type: Optional[str] = None
    discount: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    original_payment_id: Optional[int] = None
