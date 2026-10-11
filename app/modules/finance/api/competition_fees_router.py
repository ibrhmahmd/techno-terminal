"""
app/modules/finance/api/competition_fees_router.py
──────────────────────────────────────────────────
Competition fee payment and refund endpoints, moved from the competitions teams
router (ADR-0006: the workflow spans modules and lives in finance).

Paths, request bodies, responses and auth are unchanged:
  POST /teams/{team_id}/members/{student_id}/pay
  POST /teams/{team_id}/members/{student_id}/refund
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_admin
from app.modules.finance.api.deps import get_competition_fee_service
from app.api.schemas.common import ApiResponse
from app.modules.finance.api.schemas.competition_fee import PayCompetitionFeeBody, RefundCompetitionFeeBody
from app.modules.auth import User
from app.modules.finance.schemas.competition_fee import (
    PayCompetitionFeeInput,
    PayCompetitionFeeResponseDTO,
)
from app.modules.finance.services.competition_fee_service import CompetitionFeeService

router = APIRouter(tags=["Teams"])


@router.post(
    "/teams/{team_id}/members/{student_id}/pay",
    response_model=ApiResponse[PayCompetitionFeeResponseDTO],
    summary="Pay competition fee",
    description="""
    Process competition fee payment for a team member.
    Creates a receipt and records the payment. Supports partial payments.
    
    Business Rules:
    - Payment amount must be > 0
    - Payment is atomic (receipt + fee recording)
    - On failure, payment is automatically refunded
    """,
    responses={
        400: {"description": "Invalid payment amount or business rule violation"},
        404: {"description": "Team or member not found"},
    },
)
def pay_competition_fee(
    team_id: int,
    student_id: int,
    body: PayCompetitionFeeBody,
    current_user: User = Depends(require_admin),
    svc: CompetitionFeeService = Depends(get_competition_fee_service),
):
    """Process competition fee payment for a team member."""
    cmd = PayCompetitionFeeInput(
        team_id=team_id,
        student_id=student_id,
        amount=body.amount,
        parent_id=body.parent_id,
        received_by_user_id=current_user.id,
    )
    result = svc.pay_competition_fee(cmd)
    return ApiResponse(data=result, message="Payment processed successfully.")


@router.post(
    "/teams/{team_id}/members/{student_id}/refund",
    response_model=ApiResponse[bool],
    summary="Refund competition fee",
    description="""
    Refund a competition fee payment for a team member.
    Creates a refund receipt and decreases amount_paid.
    
    Business Rules:
    - Refund amount must be > 0 and <= current amount_paid
    - Refund is atomic (receipt + fee adjustment)
    - On failure, entire operation rolls back
    - Admin only
    """,
    responses={
        400: {"description": "Invalid refund amount or business rule violation"},
        404: {"description": "Team or member not found"},
    },
)
def refund_competition_fee(
    team_id: int,
    student_id: int,
    body: RefundCompetitionFeeBody,
    current_user: User = Depends(require_admin),
    svc: CompetitionFeeService = Depends(get_competition_fee_service),
):
    """Refund a competition fee payment for a team member."""
    member = svc.get_team_member(team_id, student_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found.")
    if body.amount > member.amount_paid:
        raise HTTPException(
            status_code=400,
            detail=f"Refund amount ({body.amount}) exceeds amount paid ({member.amount_paid}).",
        )
    result = svc.refund_competition_fee(
        team_member_id=member.id,
        amount=body.amount,
        current_user_id=current_user.id,
    )
    return ApiResponse(
        data=True,
        message=f"Refund of {body.amount} processed successfully with receipt {result.receipt_number}.",
    )
