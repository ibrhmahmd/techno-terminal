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
    ReceiptCreatedPublic,
    ReceiptDetailPublic,
    ReceiptListItem,
    RefundResultPublic,
    CreateReceiptRequest,
    IssueRefundRequest,
)
from app.api.schemas.finance.balance import FinancialSummaryPublic
from app.api.dependencies import require_admin, require_any, get_finance_module
from app.modules.finance.finance_schemas import ReceiptLineInput
from app.modules.auth import User

# Since finance is a flat module, we treat it similarly to `import app.modules.finance`
# but use Dependency Injection for testing flexibility.

router = APIRouter(tags=["Finance"])


# create a new receipt
@router.post(
    "/finance/receipts",
    response_model=ApiResponse[ReceiptCreatedPublic],
    status_code=201,
    summary="Create a new receipt",
)
def create_receipt(
    body: CreateReceiptRequest,
    current_user: User = Depends(require_admin),
    finance=Depends(get_finance_module),
):
    result = finance.create_receipt_with_charge_lines(
        payer_name=body.payer_name,
        method=body.method,
        received_by_user_id=current_user.id,
        lines=body.lines,
        notes=body.notes,
        allow_credit=body.allow_credit,
    )
    return ApiResponse(
        data=ReceiptCreatedPublic.model_validate(result),
        message="Receipt created successfully.",
    )


# get receipt by ID
@router.get(
    "/finance/receipts/{receipt_id}",
    response_model=ApiResponse[ReceiptDetailPublic],
    summary="Get receipt details",
)
def get_receipt(
    receipt_id: int,
    _user: User = Depends(require_any),
    finance=Depends(get_finance_module),
):
    detail = finance.get_receipt_detail(receipt_id)
    return ApiResponse(data=ReceiptDetailPublic.model_validate(detail))


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
    results = finance.search_receipts(
        from_date=from_date,
        to_date=to_date,
        payer_name_contains=payer_name,
        student_id=student_id,
        receipt_number_contains=receipt_number,
        limit=limit,
    )
    return ApiResponse(data=[ReceiptListItem.model_validate(r) for r in results])


# issue a refund
@router.post(
    "/finance/refunds",
    response_model=ApiResponse[RefundResultPublic],
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
        data=RefundResultPublic.model_validate(result),
        message="Refund issued successfully.",
    )


# get student balances
@router.get(
    "/finance/balance/student/{student_id}",
    response_model=ApiResponse[list[FinancialSummaryPublic]],
    summary="Get student balances",
)
def get_student_balance(
    student_id: int,
    _user: User = Depends(require_any),
    finance=Depends(get_finance_module),
):
    balances = finance.get_student_financial_summary(student_id)
    return ApiResponse(
        data=[FinancialSummaryPublic.model_validate(b) for b in balances]
    )


# preview overpayment risk
class PreviewRiskRequest(BaseModel):
    """Request to preview overpayment risk for receipt lines."""
    lines: list[ReceiptLineInput]


class OverpaymentRiskItem(BaseModel):
    """Risk item showing potential credit/overpayment."""
    student_id: int
    enrollment_id: int
    amount: float
    debt_before: float
    projected_balance: float
    excess_credit: float

    model_config = {"from_attributes": True}


@router.post(
    "/finance/receipts/preview-risk",
    response_model=ApiResponse[list[OverpaymentRiskItem]],
    summary="Preview overpayment risk",
)
def preview_overpayment_risk(
    body: PreviewRiskRequest,
    _user: User = Depends(require_admin),
    finance=Depends(get_finance_module),
):
    """
    Returns lines that would create/increase credit before creating a receipt.
    """
    risk_rows = finance.preview_overpayment_risk(lines=body.lines)
    return ApiResponse(data=[OverpaymentRiskItem.model_validate(r) for r in risk_rows])
