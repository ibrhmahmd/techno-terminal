"""
app/modules/finance/interfaces/dto/paginated_student_payments_dto.py
────────────────────────────────────────────────────────────────────
Paginated student payments DTO.
"""
from dataclasses import dataclass
from typing import List

from .payment_list_item_dto import PaymentListItemDTO


@dataclass(frozen=True)
class PaginatedStudentPaymentsDTO:
    """Immutable DTO for paginated student payment results."""
    items: List[PaymentListItemDTO]
    total: int
    skip: int
    limit: int
