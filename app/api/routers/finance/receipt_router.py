"""
app/api/routers/finance/receipt_router.py
─────────────────────────────────────────
API endpoints for receipt generation and management.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import require_any, require_admin
from app.api.schemas.common import ApiResponse
from app.api.schemas.finance.receipt import (
    MarkReceiptSentRequest,
    BatchGenerateRequest,
    BatchGenerateResponse,
)
from app.modules.auth.models import User
from app.modules.finance.services.receipt_generation_service import get_receipt_generation_service


router = APIRouter(tags=["Receipts"])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/receipts/{receipt_id}/generate",
    response_class=Response,
    summary="Generate receipt",
    description="Generate a formatted receipt as plain text."
)
def generate_receipt(
    receipt_id: int,
    template_name: str = Query("standard", description="Template to use (standard, detailed)"),
    include_balance: bool = Query(True, description="Include remaining balance"),
    current_user: User = Depends(require_any),
    svc = Depends(get_receipt_generation_service),
):
    """
    Generate a formatted receipt.
    
    Returns plain text receipt with:
    - Receipt number and date
    - Student and payer information
    - Payment line items
    - Totals and discounts
    - Payment method
    - Remaining balance (if requested)
    """
    content = svc.generate_receipt_text(
        receipt_id=receipt_id,
        template_name=template_name,
        include_balance=include_balance
    )
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'inline; filename="receipt_{receipt_id}.txt"'
        }
    )


@router.post(
    "/receipts/{receipt_id}/mark-sent",
    response_model=ApiResponse[dict],
    summary="Mark receipt as sent",
    description="Mark a receipt as sent to parent/guardian."
)
def mark_receipt_sent(
    receipt_id: int,
    request: MarkReceiptSentRequest,
    current_user: User = Depends(require_admin),
    svc = Depends(get_receipt_generation_service),
):
    """Mark a receipt as sent with optional email tracking."""
    receipt = svc.mark_receipt_sent(receipt_id, request.parent_email)
    
    return ApiResponse(
        data={
            "receipt_id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "sent_to_parent": receipt.sent_to_parent,
            "sent_at": receipt.sent_at.isoformat() if receipt.sent_at else None,
            "parent_email": receipt.parent_email
        },
        message="Receipt marked as sent"
    )


@router.post(
    "/receipts/batch-generate",
    response_model=ApiResponse[List[BatchGenerateResponse]],
    summary="Batch generate receipts",
    description="Generate multiple receipts at once."
)
def batch_generate_receipts(
    request: BatchGenerateRequest,
    current_user: User = Depends(require_admin),
    svc = Depends(get_receipt_generation_service),
):
    """
    Generate receipts for multiple receipt IDs.
    Useful for end-of-day batch processing.
    """
    results = svc.generate_batch_receipts(
        receipt_ids=request.receipt_ids,
        template_name=request.template_name
    )
    
    response_data = [
        BatchGenerateResponse(receipt_id=rid, content=content)
        for rid, content in results.items()
    ]
    
    return ApiResponse(
        data=response_data,
        message=f"Generated {len(response_data)} receipts"
    )
