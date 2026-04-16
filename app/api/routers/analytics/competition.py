"""
app/api/routers/analytics/competition.py
────────────────────────────────────────
Competition analytics router.

Endpoints for competition metrics: participation, fees.
"""
from fastapi import APIRouter, Depends

from app.api.schemas.common import ApiResponse, ErrorResponse
from app.modules.analytics.schemas.competition_schemas import CompetitionFeeSummaryDTO
from app.api.dependencies import require_admin, get_competition_analytics_service
from app.modules.auth import User
from app.modules.analytics.services.competition_service import CompetitionAnalyticsService

router = APIRouter(
    tags=["Analytics — Competition"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
    }
)


@router.get(
    "/analytics/competitions/fee-summary",
    response_model=ApiResponse[list[CompetitionFeeSummaryDTO]],
    summary="Get competition fee summary",
)
def get_competition_fee_summary(
    _user: User = Depends(require_admin),
    svc: CompetitionAnalyticsService = Depends(get_competition_analytics_service),
):
    """Returns participation and fee summary for all competitions."""
    return ApiResponse(data=svc.get_competition_fee_summary())
