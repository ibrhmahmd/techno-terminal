"""
app/modules/finance/schemas/overpayment_risk_item.py
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
    amount: Decimal              # the proposed payment
    debt_before: Decimal         # what the enrollment owed before it (never negative)
    projected_balance: Decimal   # balance after the payment; > 0 means credit
    excess_credit: Decimal       # the part of the payment beyond the debt
