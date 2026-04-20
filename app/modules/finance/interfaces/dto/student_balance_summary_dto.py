"""
app/modules/finance/interfaces/dto/student_balance_summary_dto.py
────────────────────────────────────────────────────────────────
Student balance summary DTO.
"""
from dataclasses import dataclass
from typing import List

from app.modules.finance.schemas import EnrollmentBalanceItem


@dataclass(frozen=True)
class StudentBalanceSummaryDTO:
    """Aggregated balance summary for a student across all enrollments."""
    student_id: int
    total_amount_due: float
    total_discounts: float
    total_paid: float
    net_balance: float
    enrollment_count: int
    unpaid_enrollments: int
    enrollments: List[EnrollmentBalanceItem]
