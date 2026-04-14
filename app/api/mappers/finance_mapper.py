"""
app/api/mappers/finance_mapper.py
──────────────────────────────────
Mapping functions to convert internal finance service DTOs
to API response DTOs.

This module provides pure functions for DTO transformations,
keeping the conversion logic separate from routers and services.
"""

from app.modules.finance.finance_schemas import (
    ReceiptSearchItem,
    EnrollmentBalanceItem,
)
from app.api.schemas.finance.receipt import ReceiptListItem
from app.api.schemas.finance.balance import StudentBalanceResponse


def to_receipt_list_item(item: ReceiptSearchItem) -> ReceiptListItem:
    """
    Convert internal ReceiptSearchItem to API ReceiptListItem.

    Field mappings:
    - id → id (already matched)
    - total is dropped (not in API schema)
    """
    return ReceiptListItem(
        id=item.id,
        receipt_number=item.receipt_number,
        payer_name=item.payer_name,
        payment_method=item.payment_method,
        paid_at=item.paid_at,
    )


def to_student_balance_response(item: EnrollmentBalanceItem) -> StudentBalanceResponse:
    """
    Convert internal EnrollmentBalanceItem to API StudentBalanceResponse.

    Field mappings:
    - amount_due → net_due
    - amount_paid → total_paid
    - remaining_balance → balance
    - group_name is set to None (not available in internal DTO)
    - student_id is added (present in finance_schemas version)
    """
    return StudentBalanceResponse(
        student_id=getattr(item, 'student_id', 0),
        group_id=item.group_id,
        enrollment_id=item.enrollment_id,
        group_name=None,  # Not available in internal DTO
        net_due=item.amount_due,
        total_paid=item.amount_paid,
        balance=item.remaining_balance,
    )
