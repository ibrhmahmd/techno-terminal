"""
app/api/routers/analytics.py
─────────────────────────────
Analytics domain router (Stub Phase 5).

Prefix: /api/v1 (mounted in main.py)
Tag:    Analytics
"""
from typing import Any
from fastapi import APIRouter, Depends

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_admin
from app.modules.auth import User

from app.modules.analytics import get_active_enrollment_count, get_today_sessions

router = APIRouter(tags=["Analytics"])


@router.get(
    "/analytics/dashboard/summary",
    response_model=ApiResponse[dict[str, Any]],
    summary="Get high-level dashboard aggregates",
)
def get_dashboard_summary(_user: User = Depends(require_admin)):
    """
    Provides a quick top-level aggregate of the system state for the admin dashboard.
    """
    active_enrollments = get_active_enrollment_count()
    today_sessions = get_today_sessions()
    
    return ApiResponse(
        data={
            "active_enrollments": active_enrollments,
            "today_sessions_count": len(today_sessions),
        },
        message="Dashboard summary loaded successfully."
    )
