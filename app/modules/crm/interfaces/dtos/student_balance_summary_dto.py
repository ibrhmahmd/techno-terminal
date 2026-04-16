"""
StudentBalanceSummaryDTO - Financial summary for a student.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentBalanceSummaryDTO:
    """Balance summary across all enrollments."""
    total_due: float
    total_discounts: float
    total_paid: float
    net_balance: float
    enrollment_count: int
    unpaid_enrollments: int
