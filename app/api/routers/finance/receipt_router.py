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
    BatchReceiptItem,
    ReceiptGenerationResponse,
)
from app.modules.auth.models import User
from app.modules.finance.services.receipt_generation_service import get_receipt_generation_service


router = APIRouter(tags=["Receipts"])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/receipts/{receipt_id}/generate",
    response_model=ApiResponse[ReceiptGenerationResponse],
    summary="Generate receipt",
    description="Generate a formatted receipt. Returns structured JSON by default. Use ?as_text=true for plain text."
)
def generate_receipt(
    receipt_id: int,
    template_name: str = Query("standard", description="Template to use (standard, detailed)"),
    include_balance: bool = Query(True, description="Include remaining balance"),
    as_text: bool = Query(False, description="Return as plain text response instead of JSON"),
    current_user: User = Depends(require_any),
    svc = Depends(get_receipt_generation_service),
):
    """
    Generates a formatted receipt.
    
    By default returns structured JSON with content and metadata (Issue M2 fixed).
    Set ?as_text=true to get plain text response for backward compatibility.
    
    The receipt includes:
    - Receipt number and date
    - Payer name
    - Line items with amounts
    - Total amount
    - Payment method
    - Remaining balance (if requested)
    """
    from datetime import datetime
    
    content = svc.generate_receipt_text(
        receipt_id=receipt_id,
        template_name=template_name,
        include_balance=include_balance
    )
    
    # Issue M2: Return structured JSON by default
    if as_text:
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'inline; filename="receipt_{receipt_id}.txt"'
            }
        )
    
    return ApiResponse(
        data=ReceiptGenerationResponse(
            receipt_id=receipt_id,
            content=content,
            template_name=template_name,
            include_balance=include_balance,
            generated_at=datetime.utcnow()
        )
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
    response_model=ApiResponse[List[BatchReceiptItem]],
    summary="Batch generate receipts",
    description="Generate multiple receipts in a single batch operation. Returns structured results with explicit success/error tracking.",
    dependencies=[Depends(require_admin)],
)
def batch_generate_receipts(
    request: BatchGenerateRequest,
    svc = Depends(get_receipt_generation_service),
):
    results = svc.generate_batch_receipts(request.receipt_ids, request.template_name)
    return ApiResponse(success=True, data=results)
