"""
app/api/routers/crm/students_history.py
───────────────────────────────────────
API endpoints for student activity and history tracking.
Refactored to use CRM StudentActivityService (SOLID architecture).
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_any, require_admin, get_student_activity_service
from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.history import (
    ActivityLogRequest,
    EnrollmentHistoryEntry,
    StatusHistoryEntry,
    CompetitionHistoryEntry,
    ActivitySummaryItem,
    ActivitySearchParams,
)
from app.api.schemas.crm.activity import (
    ActivityLogResponseDTO,
    RecentActivityItemDTO,
    ManualActivityResponseDTO,
    ActivitySearchResultItemDTO,
    ActivityReferenceDTO,
    ActivityActorDTO
)
from app.modules.auth.models import User
from app.modules.crm.services import StudentActivityService


router = APIRouter(prefix="/crm", tags=["Student History"])


# Get student activity history
@router.get(
    "/students/{student_id}/history",
    response_model=ApiResponse[List[ActivityLogResponseDTO]],
    summary="Get student activity history",
    description="Retrieve activity timeline for a specific student."
)
def get_student_history(
    student_id: int,
    activity_types: Optional[str] = Query(None, max_length=100, description="Comma-separated activity types"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
):
    """
    Get activity history for a student.
    Supports filtering by:
    - Activity types (enrollment, payment, group_change, etc.)
    - Date range
    - Pagination (limit/offset)
    """
    from app.modules.crm.interfaces.dtos.timeline_filter_dto import TimelineFilterDTO

    filters = TimelineFilterDTO(
        start_date=date_from,
        end_date=date_to,
        limit=limit,
        skip=offset,
    )

    activities = svc.get_student_timeline(
        student_id=student_id,
        filters=filters,
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


# Get summary of activities by type for a student.
@router.get(
    "/students/{student_id}/activity-summary",
    response_model=ApiResponse[List[ActivitySummaryItem]],
    summary="Get activity summary",
    description="Get summary of activities by type for a student."
)
def get_activity_summary(
    student_id: int,
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
):
    """Get activity summary (counts by type) for a student."""
    summary = svc.get_activity_summary(student_id)
    
    return ApiResponse(
        data=[ActivitySummaryItem(activity_type=type_, count=count) for type_, count in summary.activities_by_type.items()],
        message="Activity summary retrieved"
    )


# Get enrollment history for a student.
@router.get(
    "/students/{student_id}/enrollment-history",
    response_model=PaginatedResponse[EnrollmentHistoryEntry],
    summary="Get enrollment history",
    description="Get detailed enrollment history for a student."
)
def get_enrollment_history(
    student_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
):
    """Get enrollment history including transfers and level changes."""
    history, total = svc.get_enrollment_history(student_id, limit, offset)

    return PaginatedResponse(
        data=[EnrollmentHistoryEntry(
            id=h.id,
            student_id=h.student_id,
            enrollment_id=h.enrollment_id,
            group_id=h.group_id,
            group_name=h.group_name,
            level_number=h.level_number,
            enrollment_status=h.enrollment_status,
            action=h.action,
            action_date=h.action_date,
            previous_group_id=h.previous_group_id,
            previous_level_number=h.previous_level_number,
            previous_status=h.previous_status,
            amount_due=float(h.amount_due) if h.amount_due else None,
            discount_applied=float(h.discount_applied) if h.discount_applied else None,
            transfer_reason=h.transfer_reason,
            performed_by=h.performed_by,
            performed_by_name=h.performed_by_name,
            notes=h.notes
        ) for h in history],
        total=total,
        skip=offset,
        limit=limit
    )


# Get status change history for a student.
@router.get(
    "/students/{student_id}/status-history",
    response_model=PaginatedResponse[StatusHistoryEntry],
    summary="Get status history",
    description="Get status change history for a student."
)
def get_status_history(
    student_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
):
    """Get status change history for a student."""
    history, total = svc.get_status_history(student_id, limit, offset)

    return PaginatedResponse(
        data=[StatusHistoryEntry(
            id=h.id,
            student_id=h.student_id,
            old_status=h.old_status,
            new_status=h.new_status,
            changed_at=h.changed_at,
            changed_by=h.changed_by,
            changed_by_name=h.changed_by_name,
            reason=h.reason,
            notes=h.notes
        ) for h in history],
        total=total,
        skip=offset,
        limit=limit
    )


# Get competition participation history for a student.
@router.get(
    "/students/{student_id}/competition-history",
    response_model=PaginatedResponse[CompetitionHistoryEntry],
    summary="Get competition history",
    description="Get competition participation history for a student."
)
def get_competition_history(
    student_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
):
    """Get competition participation history for a student."""
    history, total = svc.get_competition_history(student_id, limit, offset)

    return PaginatedResponse(
        data=[CompetitionHistoryEntry(
            id=h.id,
            student_id=h.student_id,
            competition_id=h.competition_id,
            competition_name=h.competition_name,
            team_id=h.team_id,
            team_name=h.team_name,
            participation_type=h.participation_type,
            registration_date=h.registration_date,
            subscription_amount=float(h.subscription_amount) if h.subscription_amount else None,
            subscription_paid=h.subscription_paid,
            payment_id=h.payment_id,
            result_position=h.result_position,
            result_notes=h.result_notes,
            performed_by=h.performed_by,
            performed_by_name=h.performed_by_name,
            created_at=h.created_at
        ) for h in history],
        total=total,
        skip=offset,
        limit=limit
    )


# Manually log an activity for a student (admin only).
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
    svc: StudentActivityService = Depends(get_student_activity_service),
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


# Get recent activity across all students (admin/finance only).
@router.get(
    "/history/recent",
    response_model=ApiResponse[List[RecentActivityItemDTO]],
    summary="Get recent activity",
    description="Get recent activity across all students (admin/finance only)."
)
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
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


# Search activities with filters.
@router.post(
    "/history/search",
    response_model=ApiResponse[List[ActivitySearchResultItemDTO]],
    summary="Search activities",
    description="Search activities with filters."
)
def search_activities(
    params: ActivitySearchParams,
    current_user: User = Depends(require_any),
    svc: StudentActivityService = Depends(get_student_activity_service),
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
