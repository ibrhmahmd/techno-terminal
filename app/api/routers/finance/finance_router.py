"""
app/api/routers/finance/finance_router.py
───────────────────────────────────────
Finance domain router with SOLID-compliant dependency injection.

Endpoints:
- POST /finance/receipts              - Create new receipt
- POST /finance/refunds               - Issue refund
- GET  /finance/competition-fees      - Get unpaid competition fees
- POST /finance/risk/overpayment        - Assess overpayment risk

Prefix: /api/v1 (mounted in main.py)
Tag:    Finance
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.common import ApiResponse
from app.api.schemas.finance.receipt import (
    ReceiptCreationResponse,
    RefundResponse,
    CreateReceiptRequest,
    IssueRefundRequest,
)
from app.api.schemas.finance.risk import PreviewOverpaymentRequest, OverpaymentRiskResponse
from app.api.dependencies import (
    require_admin,
    require_any,
    get_receipt_service,
    get_refund_service,
    get_balance_service,
    get_reporting_service,
)
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.finance.services.refund_service import RefundService
from app.modules.finance.services.balance_service import BalanceService
from app.modules.finance.services.reporting_service import ReportingService
from app.modules.finance import ReceiptLineInput, UnpaidCompFeeItem
from app.modules.finance.interfaces import CreateReceiptServiceDTO, IssueRefundDTO
from app.modules.auth import User

router = APIRouter(tags=["Finance"])


@router.post(
    "/finance/receipts",
    response_model=ApiResponse[ReceiptCreationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new receipt",
    responses={
        201: {"description": "Receipt created successfully"},
        400: {"description": "Business rule violation (e.g., overpayment risk)"},
        422: {"description": "Validation error"},
    },
)
def create_receipt(
    body: CreateReceiptRequest,
    current_user: User = Depends(require_admin),
    service: ReceiptService = Depends(get_receipt_service),
) -> ApiResponse[ReceiptCreationResponse]:
    """
    Create a new receipt with payment lines.
    
    Validates for overpayment risk unless allow_credit=true.
    """
    service_lines = [
        ReceiptLineInput(
            student_id=line.student_id,
            enrollment_id=line.enrollment_id,
            team_member_id=line.team_member_id,
            amount=line.amount,
            payment_type=line.payment_type,
            discount=line.discount,
            notes=line.notes,
        )
        for line in body.lines
    ]

    result = service.create(
        CreateReceiptServiceDTO(
            lines=service_lines,
            payer_name=body.payer_name,
            payment_method=body.method,
            received_by_user_id=current_user.id,
            allow_credit=body.allow_credit,
            notes=body.notes,
        )
    )

    return ApiResponse(
        data=ReceiptCreationResponse(
            receipt_id=result.receipt_id,
            receipt_number=result.receipt_number,
            payment_method=result.payment_method,
            paid_at=result.paid_at,
            lines=len(result.lines),
            total=float(result.total),
            payment_ids=result.payment_ids,
        ),
        message="Receipt created successfully.",
    )


@router.post(
    "/finance/refunds",
    response_model=ApiResponse[RefundResponse],
    status_code=status.HTTP_200_OK,
    summary="Issue a refund",
    responses={
        200: {"description": "Refund issued successfully"},
        400: {"description": "Refund exceeds available amount"},
        404: {"description": "Original payment not found"},
    },
)
def issue_refund(
    body: IssueRefundRequest,
    current_user: User = Depends(require_admin),
    service: RefundService = Depends(get_refund_service),
) -> ApiResponse[RefundResponse]:
    """
    Issue a refund against an original payment.
    
    Creates a new receipt with a refund line. Refund amount cannot
    exceed the available amount on the original payment.
    """
    result = service.issue(
        IssueRefundDTO(
            payment_id=body.payment_id,
            amount=Decimal(str(body.amount)),
            reason=body.reason,
            received_by_user_id=current_user.id,
            method=body.method,
        )
    )

    return ApiResponse(
        data=RefundResponse(
            receipt_number=result.receipt_number,
            refunded_amount=float(result.refunded_amount),
            new_balance=float(result.new_balance) if result.new_balance else None,
        ),
        message="Refund issued successfully.",
    )

@router.get(
    "/finance/competition-fees",
    response_model=ApiResponse[list[UnpaidCompFeeItem]],
    summary="Get unpaid competition fees",
)
def get_unpaid_competition_fees(
    student_id: int = Query(..., description="Student ID to query"),
    _user: User = Depends(require_any),
    service: ReportingService = Depends(get_reporting_service),
) -> ApiResponse[list[UnpaidCompFeeItem]]:
    """
    Returns pending competition fees for a student.
    
    Used by Financial Desk to render checkbox payment lines.
    """
    fees = service.get_unpaid_competition_fees(student_id)
    return ApiResponse(data=fees)


@router.post(
    "/finance/risk/overpayment",
    response_model=ApiResponse[list[OverpaymentRiskResponse]],
    summary="Assess overpayment risk",
    responses={
        200: {"description": "Risk assessment completed"},
        422: {"description": "Validation error"},
    },
)
def assess_overpayment_risk(
    body: PreviewOverpaymentRequest,
    _user: User = Depends(require_admin),
    service: BalanceService = Depends(get_balance_service),
) -> ApiResponse[list[OverpaymentRiskResponse]]:
    """
    Assess which receipt lines would create credit/overpayment.
    
    Returns lines where projected balance after payment would be
    positive (indicating credit). Use before creating receipts to
    warn users about potential overpayments.
    """
    service_lines = [
        ReceiptLineInput(
            student_id=line.student_id,
            enrollment_id=line.enrollment_id,
            team_member_id=line.team_member_id,
            amount=line.amount,
            payment_type=line.payment_type,
            discount=line.discount,
            notes=line.notes,
        )
        for line in body.lines
    ]

    risks = service.assess_overpayment_risk(service_lines)

    return ApiResponse(
        data=[
            OverpaymentRiskResponse(
                student_id=r.student_id,
                enrollment_id=r.enrollment_id,
                amount=float(r.amount),
                debt_before=float(r.debt_before),
                projected_balance=float(r.projected_balance),
                excess_credit=float(r.excess_credit),
            )
            for r in risks
        ]
    )
