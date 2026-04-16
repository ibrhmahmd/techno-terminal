"""
app/modules/finance/interfaces/dto/enrollment_balance_dto.py
────────────────────────────────────────────────────────────
Enrollment balance DTO.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EnrollmentBalanceDTO:
    """Immutable DTO for enrollment balance data from view."""
    enrollment_id: int
    student_id: int
    group_id: int
    level_number: int
    amount_due: Decimal
    discount_applied: Decimal
    amount_paid: Decimal
    total_refunded: Decimal
    balance: Decimal
    status: str  # 'paid', 'partial', 'unpaid'
