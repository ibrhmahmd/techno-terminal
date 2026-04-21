"""
app/modules/finance/interfaces/dto/payment_list_item_dto.py
──────────────────────────────────────────────────────────
Payment list item DTO for student payments listing.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PaymentListItemDTO:
    """
    Immutable DTO for a payment in a list view.
    Contains essential payment information for display in a list.
    """
    id: int
    student_id: int
    amount: Decimal
    payment_date: datetime  # from receipt.paid_at or payment.created_at
    payment_method: Optional[str]
    status: str  # "completed" (default, can expand later)
    receipt_id: int
    receipt_number: Optional[str]
    course_name: Optional[str]
    group_name: Optional[str]
    level_number: Optional[int]
    transaction_type: str
