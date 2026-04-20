"""
app/modules/finance/interfaces/dto/paginated_enrollment_balances_dto.py
────────────────────────────────────────────────────────────────────────
Paginated enrollment balances DTO.
"""
from dataclasses import dataclass
from typing import List

from app.modules.finance.schemas import EnrollmentBalanceItem


@dataclass(frozen=True)
class PaginatedEnrollmentBalancesDTO:
    """Paginated list of enrollment balances with total count."""
    items: List[EnrollmentBalanceItem]
    total: int
