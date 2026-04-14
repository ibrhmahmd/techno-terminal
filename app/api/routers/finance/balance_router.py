"""
app/api/routers/finance/balance_router.py
─────────────────────────────────────────
API endpoints for student balance operations.
"""
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status 

from app.api.dependencies import require_any, require_admin
from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.finance.balance import (
    BalanceAdjustmentRequest,
    UnpaidEnrollmentItem,
    EnrollmentBalanceResponse,
    BalanceAdjustmentResponse,
)
from app.modules.auth.models import User
from app.modules.finance.services.balance_service import get_balance_service
from app.modules.finance.models.balance_models import (
    StudentBalanceItem,
    BalanceAdjustmentInput,
)


router = APIRouter(tags=["Student Balance"])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/students/{student_id}/balance",
    response_model=ApiResponse[StudentBalanceItem],
    summary="Get student balance",
    description="Retrieve comprehensive balance for a student including enrollment details."
)
def get_student_balance(
    student_id: int,
    use_materialized: bool = Query(True, description="Use fast materialized balance if available"),
    current_user: User = Depends(require_any),
    svc = Depends(get_balance_service),
):
    """
    Get student balance with enrollment breakdown.
    
    Returns complete financial summary including:
    - Total amount due across all enrollments
    - Total discounts applied
    - Total paid amount
    - Net balance (negative = debt, positive = credit)
    - Per-enrollment balance details
    """
    if use_materialized:
        balance = svc.get_quick_balance(student_id)
    else:
        balance = svc.calculate_balance(student_id)
    
    return ApiResponse(
        data=balance,
        message="Student balance retrieved successfully"
    )


@router.get(
    "/students/{student_id}/balance/enrollments/{enrollment_id}",
    response_model=ApiResponse[EnrollmentBalanceResponse],
    summary="Get enrollment balance",
    description="Get detailed balance for a specific enrollment."
)
def get_enrollment_balance(
    student_id: int,
    enrollment_id: int,
    current_user: User = Depends(require_any),
    svc = Depends(get_balance_service),
):
    """Get balance details for a specific enrollment."""
    balance = svc.get_enrollment_balance(enrollment_id)
    
    return ApiResponse(
        data=balance,
        message="Enrollment balance retrieved successfully"
    )


@router.get(
    "/enrollments/unpaid",
    response_model=PaginatedResponse[List[UnpaidEnrollmentItem]],
    summary="List unpaid enrollments",
    description="List all enrollments with outstanding balances, optionally filtered by group.",
)
def list_unpaid_enrollments(
    group_id: Optional[int] = Query(None, description="Filter by specific group"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    current_user: User = Depends(require_any),
    svc = Depends(get_balance_service),
):
    """
    Returns enrollments with remaining_balance > 0 (sorted by amount descending).
    
    Query params:
    - group_id: Optional filter by group
    - skip: Pagination offset
    - limit: Maximum results (default 50)
    """
    # Service now handles pagination internally (Issue M1 fixed)
    paginated, total = svc.list_unpaid_enrollments(group_id, skip=skip, limit=limit)
    
    return PaginatedResponse(
        data=paginated,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/students/{student_id}/balance/credit",
    response_model=ApiResponse[dict],
    summary="Get student credit balance",
    description="Get total available credit (overpayment) for a student."
)
def get_student_credit(
    student_id: int,
    current_user: User = Depends(require_any),
    svc = Depends(get_balance_service),
):
    """Get available credit balance for a student."""
    credit = svc.get_student_credit_balance(student_id)
    
    return ApiResponse(
        data={
            "student_id": student_id,
            "available_credit": float(credit),
            "currency": "USD"
        },
        message="Credit balance retrieved successfully"
    )


@router.post(
    "/students/{student_id}/balance/adjust",
    response_model=ApiResponse[BalanceAdjustmentResponse],
    summary="Adjust student balance",
    description="Manually adjust a student's balance (requires admin or finance role).",
    status_code=status.HTTP_200_OK,
)
def adjust_student_balance(
    student_id: int,
    request: BalanceAdjustmentRequest,
    current_user: User = Depends(require_admin),
    svc = Depends(get_balance_service),
):
    """
    Manually adjust a student's balance.
    
    This creates an adjustment record and updates the materialized balance.
    Adjustment types: manual, correction, waiver, scholarship
    
    Requires finance or admin role.
    """
    adjustment = BalanceAdjustmentInput(
        student_id=student_id,
        enrollment_id=request.enrollment_id,
        adjustment_amount=Decimal(str(request.adjustment_amount)),
        reason=request.reason,
        adjustment_type=request.adjustment_type,
        notes=request.notes
    )
    
    result = svc.adjust_balance(adjustment, performed_by=current_user.id)
    
    return ApiResponse(
        data=result,
        message="Balance adjusted successfully"
    )


@router.get(
    "/students/{student_id}/balance/summary",
    response_model=ApiResponse[dict],
    summary="Get quick balance summary",
    description="Get a simplified balance summary for quick display."
)
def get_balance_summary(
    student_id: int,
    current_user: User = Depends(require_any),
    svc = Depends(get_balance_service),
):
    """Get simplified balance summary for dashboard display."""
    balance = svc.get_quick_balance(student_id)
    
    # Calculate status
    if balance.net_balance < 0:
        status = "in_debt"
        status_display = "Payment Required"
    elif balance.net_balance > 0:
        status = "credit"
        status_display = "Credit Available"
    else:
        status = "settled"
        status_display = "Paid in Full"
    
    summary = {
        "student_id": student_id,
        "total_due": balance.total_amount_due,
        "total_paid": balance.total_paid,
        "net_balance": abs(balance.net_balance),
        "balance_type": status,  # 'in_debt', 'credit', 'settled'
        "balance_status": status_display,
        "active_enrollments": len([e for e in balance.enrollment_details if e.status != 'paid']),
        "as_of_date": balance.as_of_date.isoformat()
    }
    
    return ApiResponse(
        data=summary,
        message="Balance summary retrieved successfully"
    )
