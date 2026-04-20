"""
app/api/routers/finance/finance_router.py
───────────────────────────────────────
Finance domain router with SOLID-compliant dependency injection.

Endpoints:
- POST /finance/receipts              - Create new receipt
- POST /finance/refunds               - Issue refund
- GET  /finance/competition-fees      - Get unpaid competition fees
- POST /finance/risk/overpayment        - Assess overpayment risk
- GET  /students/{id}/balance           - Get student balance summary
- GET  /balance/unpaid-enrollments      - List unpaid enrollments

Prefix: /api/v1 (mounted in main.py)
Tag:    Finance
"""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, BackgroundTasks

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.finance.receipt import (
    ReceiptCreationResponse,
    RefundResponse,
    CreateReceiptRequest,
    IssueRefundRequest,
)
from app.api.schemas.finance.risk import PreviewOverpaymentRequest, OverpaymentRiskResponse
from app.api.schemas.finance.balance import (
    StudentBalanceResponse,
    EnrollmentBalanceResponse,
    UnpaidEnrollmentItem,
)
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
    background_tasks: BackgroundTasks,
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
        ),
        background_tasks=background_tasks
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


@router.get(
    "/students/{student_id}/balance",
    response_model=ApiResponse[StudentBalanceResponse],
    summary="Get student balance summary",
)
def get_student_balance(
    student_id: int,
    _user: User = Depends(require_any),
    service: BalanceService = Depends(get_balance_service),
) -> ApiResponse[StudentBalanceResponse]:
    """
    Get comprehensive balance summary for a student across all enrollments.
    
    Returns aggregated totals and per-enrollment breakdown.
    """
    summary = service.get_student_balance_summary(student_id)
    
    # Convert enrollment items to response schema
    enrollments = [
        EnrollmentBalanceResponse(
            enrollment_id=e.enrollment_id,
            student_id=e.student_id,
            group_id=e.group_id,
            level_number=e.level_number,
            amount_due=e.amount_due,
            discount_applied=e.discount_applied,
            total_paid=e.amount_paid,
            total_refunded=0.0,  # Not tracked per enrollment in current view
            remaining_balance=e.remaining_balance,
            status=e.status,
            is_paid=e.remaining_balance >= 0,
        )
        for e in summary.enrollments
    ]
    
    return ApiResponse(
        data=StudentBalanceResponse(
            student_id=summary.student_id,
            total_amount_due=summary.total_amount_due,
            total_discounts=summary.total_discounts,
            total_paid=summary.total_paid,
            net_balance=summary.net_balance,
            enrollment_count=summary.enrollment_count,
            unpaid_enrollments=summary.unpaid_enrollments,
            enrollments=enrollments,
        )
    )


@router.get(
    "/balance/unpaid-enrollments",
    response_model=PaginatedResponse[UnpaidEnrollmentItem],
    summary="List unpaid enrollments",
)
def get_unpaid_enrollments(
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Records per page"),
    _user: User = Depends(require_any),
    service: BalanceService = Depends(get_balance_service),
) -> PaginatedResponse[UnpaidEnrollmentItem]:
    """
    Get all unpaid enrollments across all students.
    
    Unpaid = remaining_balance < 0 (debt).
    Supports pagination and optional group filtering.
    """
    result = service.get_unpaid_enrollments(
        group_id=group_id, skip=skip, limit=limit
    )
    
    # Convert to response schema
    response_items = [
        UnpaidEnrollmentItem(
            enrollment_id=item.enrollment_id,
            student_id=item.student_id,
            student_name="",  # Not available in current view
            group_id=item.group_id,
            group_name="",  # Not available in current view
            course_name=None,  # Not available in current view
            level_number=item.level_number,
            amount_due=item.amount_due,
            discount_applied=item.discount_applied,
            total_paid=item.amount_paid,
            remaining_balance=item.remaining_balance,
            enrolled_at=None,  # Not available in current view
        )
        for item in result.items
    ]
    
    return PaginatedResponse(
        data=response_items,
        total=result.total,
        skip=skip,
        limit=limit,
    )
