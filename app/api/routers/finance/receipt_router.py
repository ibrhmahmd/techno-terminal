"""
app/api/routers/finance/receipt_router.py
─────────────────────────────────────────
API endpoints for receipt generation and management.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, HTTPException

from app.api.dependencies import (
    require_any,
    require_admin,
    get_receipt_service,
)
from app.api.schemas.common import ApiResponse
from app.api.schemas.finance.receipt import (
    BatchGenerateRequest,
    BatchReceiptItem,
    ReceiptGenerationResponse,
    ReceiptDetailResponse,
    ReceiptListItem,
)
from app.api.mappers.finance_mapper import to_receipt_list_item, to_receipt_detail_response
from app.modules.auth.models import User
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.finance.services.receipt_generation_service import get_receipt_generation_service
from app.modules.finance.interfaces import SearchReceiptsDTO
from app.shared.exceptions import NotFoundError


router = APIRouter(tags=["Receipts"])


@router.get(
    "/finance/receipts/{receipt_id}",
    response_model=ApiResponse[ReceiptDetailResponse],
    summary="Get receipt details",
)
def get_receipt(
    receipt_id: int,
    _user: User = Depends(require_any),
    service: ReceiptService = Depends(get_receipt_service),
):
    detail = service.get_detail(receipt_id)
    if detail is None:
        raise NotFoundError("Receipt not found")
    return ApiResponse(data=to_receipt_detail_response(detail))


@router.get(
    "/finance/receipts",
    response_model=ApiResponse[list[ReceiptListItem]],
    summary="Search receipts",
)
def search_receipts(
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    payer_name: Optional[str] = Query(None, description="Filter by payer name"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    receipt_number: Optional[str] = Query(None, description="Filter by receipt number"),
    limit: int = Query(200, le=1000),
    _user: User = Depends(require_admin),
    service: ReceiptService = Depends(get_receipt_service),
):
    max_days = 90
    date_range = (to_date - from_date).days
    if date_range > max_days:
        raise HTTPException(
            status_code=422,
            detail=f"Date range too large. Maximum allowed is {max_days} days. Requested: {date_range} days.",
        )

    results = service.search(
        SearchReceiptsDTO(
            from_date=from_date,
            to_date=to_date,
            payer_name_contains=payer_name,
            student_id=student_id,
            receipt_number_contains=receipt_number,
            limit=limit,
        )
    )
    return ApiResponse(data=[to_receipt_list_item(r) for r in results])


@router.get(
    "/finance/receipts/{receipt_id}/pdf",
    summary="Download PDF receipt",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "Returns the PDF document"}},
)
def download_receipt_pdf(
    receipt_id: int,
    _user: User = Depends(require_any),
    service: ReceiptService = Depends(get_receipt_service),
):
    detail = service.get_detail(receipt_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Receipt not found")
    pdf_bytes = service.generate_pdf(receipt_id)
    receipt_number = detail.receipt.receipt_number if detail.receipt else None
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="receipt_{receipt_number or receipt_id}.pdf"'},
    )


@router.get(
    "/finance/receipts/{receipt_id}/generate",
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
    "/finance/receipts/batch-generate",
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
