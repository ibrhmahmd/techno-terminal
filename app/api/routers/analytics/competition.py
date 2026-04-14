"""
app/api/routers/analytics/competition.py
────────────────────────────────────────
Competition analytics router.

Endpoints for competition metrics: participation, fees.
"""
from fastapi import APIRouter, Depends

from app.api.schemas.common import ApiResponse
from app.api.schemas.analytics import CompetitionFeeSummaryResponse
from app.api.dependencies import require_admin, get_competition_analytics_service
from app.modules.auth import User
from app.modules.analytics.services.competition_service import CompetitionAnalyticsService

router = APIRouter(tags=["Analytics — Competition"])


@router.get(
    "/analytics/competitions/fee-summary",
    response_model=ApiResponse[list[CompetitionFeeSummaryResponse]],
    summary="Get competition fee summary",
)
def get_competition_fee_summary(
    _user: User = Depends(require_admin),
    svc: CompetitionAnalyticsService = Depends(get_competition_analytics_service),
):
    """Returns participation and fee summary for all competitions."""
    return ApiResponse(data=svc.get_competition_fee_summary())
