"""
app/modules/crm/interfaces/dtos/log_payment_dto.py
───────────────────────────────────────────────────
DTO for logging payment activities.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class LogPaymentDTO:
    """Immutable DTO for logging payment activities."""
    student_id: int
    payment_id: int
    amount: Decimal
    payment_type: str
    performed_by: Optional[int] = None
