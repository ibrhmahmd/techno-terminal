"""
app/api/mappers/finance_mapper.py
──────────────────────────────────
Mapping functions to convert internal finance service DTOs
to API response DTOs.

This module provides pure functions for DTO transformations,
keeping the conversion logic separate from routers and services.
"""

from app.modules.finance import ReceiptSearchItem
from app.api.schemas.finance.receipt import ReceiptListItem


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
