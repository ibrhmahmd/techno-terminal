"""
app/api/routers/analytics/dashboard.py
─────────────────────────────────────
Dashboard analytics router.

Endpoints for the admin dashboard daily overview API.
"""

from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.schemas.common import ApiResponse, ErrorResponse
from app.modules.analytics.schemas.dashboard_schemas import DashboardDailyOverviewDTO
from app.api.dependencies import require_admin, get_dashboard_service
from app.modules.auth import User
from app.modules.analytics.services.dashboard_service import DashboardService

router = APIRouter(
    tags=["Analytics — Dashboard"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Missing or invalid token"},
        403: {"model": ErrorResponse, "description": "Forbidden - Insufficient permissions"},
        422: {"model": ErrorResponse, "description": "Validation Error - Invalid parameters"},
    }
)


@router.get(
    "/dashboard/daily-overview",
    response_model=ApiResponse[DashboardDailyOverviewDTO],
    summary="Get daily dashboard overview",
)
def get_daily_overview(
    date_param: date = Query(..., alias="date", description="Target date (YYYY-MM-DD)"),
    include_attendance: bool = Query(True, description="Include full attendance grid data"),
    _user: User = Depends(require_admin),
    svc: DashboardService = Depends(get_dashboard_service),
):
    """
    Get daily dashboard overview for the specified date.
    
    Returns:
    - Lookup tables for groups and instructors (deduplicated)
    - Scheduled groups with sessions on the target date
    - Full session history for each group's current level
    - Attendance data (if include_attendance=true)
    - Summary statistics
    
    The response uses a lookup table pattern where group and instructor
    metadata appears once in lookup tables, referenced by ID from the
    scheduled_groups array.
    
    Groups are sorted by default_time_start (earliest first).
    """
    try:
        result = svc.get_daily_overview(date_param, include_attendance)
        return ApiResponse(
            data=result,
            message="Dashboard overview loaded successfully.",
        )
    except Exception as e:
        # Log the error and return a generic error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard overview: {str(e)}"
        )
