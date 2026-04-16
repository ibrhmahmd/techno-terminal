"""
app/api/mappers/finance_mapper.py
──────────────────────────────────
Mapping functions to convert internal finance service DTOs
to API response DTOs.

This module provides pure functions for DTO transformations,
keeping the conversion logic separate from routers and services.
"""

from app.modules.finance import ReceiptSearchItem
from app.modules.finance.interfaces.dto import ReceiptDetailDTO
from app.api.schemas.finance.receipt import (
    ReceiptListItem,
    ReceiptDetailResponse,
    ReceiptHeaderResponse,
    ReceiptLineResponse,
)


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


def to_receipt_detail_response(detail: ReceiptDetailDTO) -> ReceiptDetailResponse:
    """
    Convert ReceiptDetailDTO to ReceiptDetailResponse.

    Field mappings:
    - detail.receipt → receipt (validated with model_validate)
    - detail.lines → lines (mapped individually)
    - detail.total → total (converted to float)
    """
    return ReceiptDetailResponse(
        receipt=ReceiptHeaderResponse.model_validate(detail.receipt),
        lines=[
            ReceiptLineResponse(
                id=line.id,
                student_id=line.student_id,
                enrollment_id=line.enrollment_id,
                amount=float(line.amount),
                transaction_type=line.transaction_type,
                payment_type=line.payment_type,
                discount=float(line.discount),
                notes=line.notes,
            )
            for line in detail.lines
        ],
        total=float(detail.total),
    )
