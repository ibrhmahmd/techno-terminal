"""
app/api/routers/finance.py
───────────────────────────
Finance domain router.

Prefix: /api/v1 (mounted in main.py)
Tag:    Finance
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.schemas.finance.receipt import (
    ReceiptCreationResponse,
    ReceiptDetailResponse,
    ReceiptListItem,
    RefundResponse,
    CreateReceiptRequest,
    IssueRefundRequest,
    ReceiptLineRequest,
)
from app.api.schemas.finance.balance import StudentBalanceResponse
from app.api.schemas.finance.risk import PreviewOverpaymentRequest, OverpaymentRiskResponse
from app.api.dependencies import require_admin, require_any, get_finance_module
from app.modules.finance.finance_schemas import ReceiptLineInput
from app.modules.auth import User
from app.shared.exceptions import NotFoundError
from app.api.mappers.finance_mapper import (
    to_receipt_list_item,
    to_student_balance_response,
)

# Since finance is a flat module, we treat it similarly to `import app.modules.finance`
# but use Dependency Injection for testing flexibility.

router = APIRouter(tags=["Finance"])


# create a new receipt
@router.post(
    "/finance/receipts",
    response_model=ApiResponse[ReceiptCreationResponse],
    status_code=201,
    summary="Create a new receipt",
)
def create_receipt(
    body: CreateReceiptRequest,
    current_user: User = Depends(require_admin),
    finance=Depends(get_finance_module),
):
    # Convert API DTOs to internal service DTOs
    service_lines = [
        ReceiptLineInput(
            student_id=line.student_id,
            enrollment_id=line.enrollment_id,
            amount=line.amount,
            payment_type=line.payment_type,
            discount=line.discount,
            notes=line.notes,
        )
        for line in body.lines
    ]
    
    result = finance.create_receipt_with_charge_lines(
        payer_name=body.payer_name,
        method=body.method,
        received_by_user_id=current_user.id,
        lines=service_lines,
        notes=body.notes,
        allow_credit=body.allow_credit,
    )
    return ApiResponse(
        data=ReceiptCreationResponse(
            receipt_id=result.receipt_id,
            receipt_number=result.receipt_number,
            payment_method=result.payment_method,
            paid_at=result.paid_at,
            lines=len(result.lines),
            total=result.total,
            payment_ids=result.payment_ids,
        ),
        message="Receipt created successfully.",
    )


# get receipt by ID
@router.get(
    "/finance/receipts/{receipt_id}",
    response_model=ApiResponse[ReceiptDetailResponse],
    summary="Get receipt details",
)
def get_receipt(
    receipt_id: int,
    _user: User = Depends(require_any),
    finance=Depends(get_finance_module),
):
    detail = finance.get_receipt_detail(receipt_id)
    if detail is None:
        raise NotFoundError("Receipt not found")
    return ApiResponse(data=ReceiptDetailResponse.model_validate(detail))


# search receipts
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
    finance=Depends(get_finance_module),
):
    # Validate date range doesn't exceed 90 days (Issue M3)
    max_days = 90
    date_range = (to_date - from_date).days
    if date_range > max_days:
        raise HTTPException(
            status_code=422,
            detail=f"Date range too large. Maximum allowed is {max_days} days. Requested: {date_range} days."
        )
    
    results = finance.search_receipts(
        from_date=from_date,
        to_date=to_date,
        payer_name_contains=payer_name,
        student_id=student_id,
        receipt_number_contains=receipt_number,
        limit=limit,
    )
    return ApiResponse(data=[to_receipt_list_item(r) for r in results])


# issue a refund
@router.post(
    "/finance/refunds",
    response_model=ApiResponse[RefundResponse],
    summary="Issue a refund",
)
def issue_refund(
    body: IssueRefundRequest,
    current_user: User = Depends(require_admin),
    finance=Depends(get_finance_module),
):
    result = finance.issue_refund(
        payment_id=body.payment_id,
        amount=body.amount,
        reason=body.reason,
        received_by_user_id=current_user.id,
        method=body.method,
    )
    return ApiResponse(
        data=RefundResponse.model_validate(result),
        message="Refund issued successfully.",
    )


# get student balances
@router.get(
    "/finance/balance/student/{student_id}",
    response_model=ApiResponse[list[StudentBalanceResponse]],
    summary="Get student balances",
)
def get_student_balance(
    student_id: int,
    _user: User = Depends(require_any),
    finance=Depends(get_finance_module),
):
    balances = finance.get_student_financial_summary(student_id)
    return ApiResponse(
        data=[to_student_balance_response(b) for b in balances]
    )


from app.modules.finance.finance_schemas import UnpaidCompFeeItem

@router.get(
    "/finance/competition-fees/student/{student_id}",
    response_model=ApiResponse[list[UnpaidCompFeeItem]],
    summary="Get unpaid competition fees",
)
def get_unpaid_competition_fees(
    student_id: int,
    _user: User = Depends(require_any),
    finance=Depends(get_finance_module),
):
    """
    Returns pending competition fees for a student to be paid via Financial Desk setup.
    """
    fees = finance.get_unpaid_competition_fees(student_id)
    return ApiResponse(
        data=[UnpaidCompFeeItem.model_validate(f) for f in fees]
    )


@router.post(
    "/finance/receipts/preview-risk",
    response_model=ApiResponse[list[OverpaymentRiskResponse]],
    summary="Preview overpayment risk",
)
def preview_overpayment_risk(
    body: PreviewOverpaymentRequest,
    _user: User = Depends(require_admin),
    finance=Depends(get_finance_module),
):
    """
    Returns lines that would create/increase credit before creating a receipt.
    """
    # Convert API DTOs to internal service DTOs
    service_lines = [
        ReceiptLineInput(
            student_id=line.student_id,
            enrollment_id=line.enrollment_id,
            amount=line.amount,
            payment_type=line.payment_type,
            discount=line.discount,
            notes=line.notes,
        )
        for line in body.lines
    ]
    
    risk_rows = finance.preview_overpayment_risk(lines=service_lines)
    return ApiResponse(data=[OverpaymentRiskResponse.model_validate(r) for r in risk_rows])


from fastapi.responses import Response
from fastapi import HTTPException

@router.get(
    "/finance/receipts/{receipt_id}/pdf",
    summary="Download PDF receipt",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the PDF document",
        }
    }
)
def download_receipt_pdf(
    receipt_id: int,
    _user: User = Depends(require_any),
    finance=Depends(get_finance_module),
):
    """
    Generate a branded PDF receipt with optional logo and signatures.
    """
    receipt = finance.get_receipt_detail(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    pdf_bytes = finance.generate_receipt_pdf(receipt_id)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="receipt_{receipt.receipt_number or receipt_id}.pdf"'
        }
    )
