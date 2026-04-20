"""
app/api/routers/finance/reporting_router.py
───────────────────────────────────────────
Financial reporting router for daily collections and receipts.

Endpoints:
- GET /finance/reports/daily-collections  - Daily collection summary by payment method
- GET /finance/reports/daily-receipts     - All receipts issued on a specific date

Prefix: /api/v1 (mounted in main.py)
Tag:    Finance — Reporting
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_admin, get_reporting_service
from app.modules.auth import User
from app.modules.finance.services.reporting_service import ReportingService
from app.modules.finance.schemas import DailyCollectionItem, DailyReceiptItem

router = APIRouter(tags=["Finance — Reporting"])


@router.get(
    "/finance/reports/daily-collections",
    response_model=ApiResponse[list[DailyCollectionItem]],
    status_code=status.HTTP_200_OK,
    summary="Get daily collection summary",
    responses={
        200: {"description": "Daily collection summary retrieved"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - admin access required"},
    },
)
def get_daily_collections(
    target_date: Optional[date] = Query(None, description="Target date (default: today)"),
    _user: User = Depends(require_admin),
    service: ReportingService = Depends(get_reporting_service),
) -> ApiResponse[list[DailyCollectionItem]]:
    """
    Get daily collection summary grouped by payment method.
    
    Returns totals for each payment method used on the specified date,
    including receipt count and total amount collected.
    """
    collections = service.get_daily_collections(target_date)
    return ApiResponse(data=collections)


@router.get(
    "/finance/reports/daily-receipts",
    response_model=ApiResponse[list[DailyReceiptItem]],
    status_code=status.HTTP_200_OK,
    summary="Get daily receipts listing",
    responses={
        200: {"description": "Daily receipts listing retrieved"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - admin access required"},
    },
)
def get_daily_receipts(
    target_date: Optional[date] = Query(None, description="Target date (default: today)"),
    _user: User = Depends(require_admin),
    service: ReportingService = Depends(get_reporting_service),
) -> ApiResponse[list[DailyReceiptItem]]:

    """
    Get all receipts issued on a specific date.
    
    Returns a list of all receipts created on the specified date,
    including receipt number, payer name, amount, and payment method.
    """
    receipts = service.get_daily_receipts(target_date)
    return ApiResponse(data=receipts)
