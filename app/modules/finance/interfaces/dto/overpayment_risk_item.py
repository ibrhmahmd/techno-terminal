"""
app/modules/finance/interfaces/dto/overpayment_risk_item.py
────────────────────────────────────────────────────────────
Overpayment risk item DTO.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OverpaymentRiskItem:
    """Immutable DTO for overpayment risk assessment."""
    student_id: int
    enrollment_id: int
    proposed_charge: Decimal
    current_balance: Decimal
    projected_balance: Decimal
    risk_level: str  # 'none', 'low', 'medium', 'high'
