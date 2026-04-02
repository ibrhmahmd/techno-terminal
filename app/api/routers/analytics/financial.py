"""
app/api/routers/analytics/financial.py
──────────────────────────────────────
Financial analytics router.

Endpoints for financial metrics: revenue, outstanding balances, debtors.
"""
from datetime import date
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_admin, get_financial_analytics_service
from app.modules.auth import User

from app.modules.analytics.schemas import (
    RevenueByDateDTO,
    RevenueByMethodDTO,
    OutstandingByGroupDTO,
    TopDebtorDTO,
)
from app.modules.analytics.services.financial_service import FinancialAnalyticsService

router = APIRouter(tags=["Analytics — Financial"])


@router.get(
    "/analytics/finance/revenue-by-date",
    response_model=ApiResponse[list[RevenueByDateDTO]],
    summary="Get revenue breakdown by date",
)
def get_revenue_by_date(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    _user: User = Depends(require_admin),
    svc: FinancialAnalyticsService = Depends(get_financial_analytics_service),
):
    """Returns daily revenue totals within the specified date range."""
    return ApiResponse(data=svc.get_revenue_by_date(start, end))


@router.get(
    "/analytics/finance/revenue-by-method",
    response_model=ApiResponse[list[RevenueByMethodDTO]],
    summary="Get revenue breakdown by payment method",
)
def get_revenue_by_method(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    _user: User = Depends(require_admin),
    svc: FinancialAnalyticsService = Depends(get_financial_analytics_service),
):
    """Returns revenue totals grouped by payment method within the date range."""
    return ApiResponse(data=svc.get_revenue_by_method(start, end))


@router.get(
    "/analytics/finance/outstanding-by-group",
    response_model=ApiResponse[list[OutstandingByGroupDTO]],
    summary="Get outstanding balances by group",
)
def get_outstanding_by_group(
    _user: User = Depends(require_admin),
    svc: FinancialAnalyticsService = Depends(get_financial_analytics_service),
):
    """Returns outstanding balance totals grouped by academic group."""
    return ApiResponse(data=svc.get_outstanding_by_group())


@router.get(
    "/analytics/finance/top-debtors",
    response_model=ApiResponse[list[TopDebtorDTO]],
    summary="Get top debtors",
)
def get_top_debtors(
    limit: int = Query(15, ge=1, le=100, description="Number of results to return"),
    _user: User = Depends(require_admin),
    svc: FinancialAnalyticsService = Depends(get_financial_analytics_service),
):
    """Returns students with highest outstanding balances."""
    return ApiResponse(data=svc.get_top_debtors(limit))
