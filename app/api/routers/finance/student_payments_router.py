"""
app/api/routers/finance/student_payments_router.py
──────────────────────────────────────────────────
Student payments router (Finance module).

Endpoint for listing student payment history.
Moved from CRM module to Finance module per ADR-0006 (cross-module writes live in highest module).
"""
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import PaginatedResponse
from app.api.schemas.finance.payment import PaymentListItem
from app.api.dependencies import require_any, get_student_payment_service
from app.modules.finance.services.student_payment_service import StudentPaymentService
from app.modules.auth import User

router = APIRouter(prefix="/crm", tags=["CRM — Students"])


@router.get(
    "/students/{student_id}/payments",
    response_model=PaginatedResponse[PaymentListItem],
    summary="List student payments",
    description="Retrieve all payment records for a specific student with course and group information.",
)
def list_student_payments(
    student_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: StudentPaymentService = Depends(get_student_payment_service),
):
    """
    List all payments for a specific student.

    Returns paginated payment history including:
    - Payment amount and date
    - Receipt number and payment method
    - Course name and group name (if applicable)

    Sorted by payment date descending (newest first).
    """
    result = svc.list_student_payments(student_id=student_id, skip=skip, limit=limit)
    return PaginatedResponse(
        data=[PaymentListItem.model_validate(item) for item in result.items],
        total=result.total,
        skip=result.skip,
        limit=result.limit,
    )