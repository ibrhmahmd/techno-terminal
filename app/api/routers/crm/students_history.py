"""
app/api/routers/crm/students_history.py
───────────────────────────────────────
API endpoints for student activity and history tracking.
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_any, require_admin
from app.api.schemas.common import ApiResponse
from app.api.schemas.students.history import (
    ActivityLogRequest,
    EnrollmentHistoryEntry,
    ActivitySummaryItem,
    ActivitySearchParams,
)
from app.api.schemas.students.activity import (
    ActivityLogResponseDTO,
    RecentActivityItemDTO,
    ManualActivityResponseDTO,
    ActivitySearchResultItemDTO,
    ActivityReferenceDTO,
    ActivityActorDTO
)
from app.modules.auth.models import User
from app.modules.students.services.activity_service import get_activity_service


router = APIRouter(tags=["Student History"])


# Get student activity history
@router.get(
    "/students/{student_id}/history",
    response_model=ApiResponse[List[ActivityLogResponseDTO]],
    summary="Get student activity history",
    description="Retrieve activity timeline for a specific student."
)
def get_student_history(
    student_id: int,
    activity_types: Optional[str] = Query(None, description="Comma-separated activity types"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_any),
    svc = Depends(get_activity_service),
):
    """
    Get activity history for a student.
    
    Supports filtering by:
    - Activity types (enrollment, payment, group_change, etc.)
    - Date range
    - Pagination (limit/offset)
    """
    # Parse activity types
    type_list = activity_types.split(",") if activity_types else None
    
    activities = svc.get_student_activity_timeline(
        student_id=student_id,
        activity_types=type_list,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    return ApiResponse(
        data=[ActivityLogResponseDTO(
            activity_id=a.id,
            student_id=a.student_id,
            activity_type=a.activity_type,
            activity_subtype=a.activity_subtype,
            description=a.description,
            reference=ActivityReferenceDTO(
                reference_type=a.reference_type,
                reference_id=a.reference_id
            ) if a.reference_type and a.reference_id else None,
            performed_by=ActivityActorDTO(user_id=a.performed_by) if a.performed_by else None,
            meta=a.metadata,
            created_at=a.created_at.isoformat() if a.created_at else None
        ) for a in activities],
        message=f"Retrieved {len(activities)} activities"
    )


# 
@router.get(
    "/students/{student_id}/activity-summary",
    response_model=ApiResponse[List[ActivitySummaryItem]],
    summary="Get activity summary",
    description="Get summary of activities by type for a student."
)
def get_activity_summary(
    student_id: int,
    current_user: User = Depends(require_any),
    svc = Depends(get_activity_service),
):
    """Get activity summary (counts by type) for a student."""
    summary = svc.get_activity_summary(student_id)
    
    return ApiResponse(
        data=[ActivitySummaryItem(activity_type=type_, count=count) for type_, count in summary.items()],
        message="Activity summary retrieved"
    )


@router.get(
    "/students/{student_id}/enrollment-history",
    response_model=ApiResponse[List[EnrollmentHistoryEntry]],
    summary="Get enrollment history",
    description="Get detailed enrollment history for a student."
)
def get_enrollment_history(
    student_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_any),
    svc = Depends(get_activity_service),
):
    """Get enrollment history including transfers and level changes."""
    history = svc.get_enrollment_history(student_id, limit)
    
    return ApiResponse(
        data=[EnrollmentHistoryEntry(
            id=h.id,
            student_id=h.student_id,
            enrollment_id=h.enrollment_id,
            group_id=h.group_id,
            level_number=h.level_number,
            action=h.action,
            action_date=h.action_date,
            previous_group_id=h.previous_group_id,
            previous_level_number=h.previous_level_number,
            amount_due=h.amount_due,
            amount_paid=h.amount_paid,
            final_status=h.final_status,
            notes=h.notes
        ) for h in history],
        message=f"Retrieved {len(history)} enrollment history entries"
    )


@router.post(
    "/students/{student_id}/log-activity",
    response_model=ApiResponse[ManualActivityResponseDTO],
    summary="Log manual activity",
    description="Manually log an activity for a student (admin only)."
)
def log_manual_activity(
    student_id: int,
    request: ActivityLogRequest,
    current_user: User = Depends(require_admin),
    svc = Depends(get_activity_service),
):
    """Manually log an activity entry."""
    activity = svc.log_activity(
        student_id=student_id,
        activity_type=request.activity_type,
        activity_subtype=request.activity_subtype,
        reference_type=request.reference_type,
        reference_id=request.reference_id,
        description=request.description,
        metadata=request.metadata,
        performed_by=current_user.id
    )
    
    return ApiResponse(
        data=ManualActivityResponseDTO(
            activity_id=activity.id,
            student_id=activity.student_id,
            activity_type=activity.activity_type,
            description=activity.description or "",
            created_at=activity.created_at.isoformat() if activity.created_at else None
        ),
        message="Activity logged successfully"
    )


@router.get(
    "/history/recent",
    response_model=ApiResponse[List[RecentActivityItemDTO]],
    summary="Get recent activity",
    description="Get recent activity across all students (admin/finance only)."
)
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_any),
    svc = Depends(get_activity_service),
):
    """Get recent activity feed for admin dashboard."""
    activities = svc.get_recent_activity(limit)
    
    return ApiResponse(
        data=[RecentActivityItemDTO(
            activity_id=a.id,
            student_id=a.student_id,
            activity_type=a.activity_type,
            description=a.description or "",
            created_at=a.created_at.isoformat() if a.created_at else None,
            performed_by_name=getattr(a, 'performed_by_name', None)
        ) for a in activities],
        message=f"Retrieved {len(activities)} recent activities"
    )


@router.post(
    "/history/search",
    response_model=ApiResponse[List[ActivitySearchResultItemDTO]],
    summary="Search activities",
    description="Search activities with filters."
)
def search_activities(
    params: ActivitySearchParams,
    current_user: User = Depends(require_any),
    svc = Depends(get_activity_service),
):
    """Search activities with various filters."""
    activities = svc.search_activities(
        search_term=params.search_term,
        activity_types=params.activity_types,
        date_from=params.date_from,
        date_to=params.date_to,
        performed_by=params.performed_by,
        student_id=params.student_id,
        limit=params.limit
    )
    
    return ApiResponse(
        data=[ActivitySearchResultItemDTO(
            activity_id=a.id,
            student_id=a.student_id,
            activity_type=a.activity_type,
            description=a.description or "",
            meta=a.metadata,
            created_at=a.created_at.isoformat() if a.created_at else None
        ) for a in activities],
        message=f"Found {len(activities)} activities"
    )
