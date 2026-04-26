"""
app/api/routers/analytics/academic.py
─────────────────────────────────────
Academic analytics router.

Endpoints for academic metrics: enrollments, sessions, attendance.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, ErrorResponse
from app.modules.analytics.schemas.academic_schemas import (
    UnpaidAttendeeDTO,
    AttendanceHeatmapRowDTO,
    StudentProgressDTO,
    CourseCompletionDTO,
)
from app.api.dependencies import require_admin, get_academic_analytics_service
from app.modules.auth import User
from app.modules.analytics.services.academic_service import AcademicAnalyticsService

router = APIRouter(
    tags=["Analytics — Academic"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Missing or invalid token"},
        403: {"model": ErrorResponse, "description": "Forbidden - Insufficient permissions"},
        422: {"model": ErrorResponse, "description": "Validation Error - Invalid parameters"},
    }
)


@router.get(
    "/analytics/academics/unpaid-attendees",
    response_model=ApiResponse[list[UnpaidAttendeeDTO]],
    summary="Get unpaid attendees for today",
)
def get_unpaid_attendees(
    target_date: Optional[date] = None,
    _user: User = Depends(require_admin),
    svc: AcademicAnalyticsService = Depends(get_academic_analytics_service),
):
    """Returns students attending sessions today who have unpaid balances."""
    return ApiResponse(data=svc.get_today_unpaid_attendees(target_date))


@router.get(
    "/analytics/academics/groups/{group_id}/heatmap",
    response_model=ApiResponse[list[AttendanceHeatmapRowDTO]],
    summary="Get attendance heatmap for group",
)
def get_attendance_heatmap(
    group_id: int,
    level_number: int = Query(..., ge=1, description="Level number"),
    _user: User = Depends(require_admin),
    svc: AcademicAnalyticsService = Depends(get_academic_analytics_service),
):
    """Returns attendance heatmap (student x date matrix) for a group."""
    return ApiResponse(data=svc.get_attendance_heatmap(group_id, level_number))


@router.get(
    "/analytics/academics/student-progress",
    response_model=ApiResponse[list[StudentProgressDTO]],
    summary="Get student progress analytics",
)
def get_student_progress(
    student_id: Optional[int] = Query(None, description="Filter by specific student ID"),
    group_id: Optional[int] = Query(None, description="Filter by specific group ID"),
    _user: User = Depends(require_admin),
    svc: AcademicAnalyticsService = Depends(get_academic_analytics_service),
):
    """Returns student progress analytics including attendance % and progress status.
    
    Can be filtered by student_id and/or group_id, or returns all active enrollments if no filters provided.
    """
    return ApiResponse(data=svc.get_student_progress(student_id, group_id))


@router.get(
    "/analytics/academics/course-completion",
    response_model=ApiResponse[list[CourseCompletionDTO]],
    summary="Get course completion rates",
)
def get_course_completion(
    _user: User = Depends(require_admin),
    svc: AcademicAnalyticsService = Depends(get_academic_analytics_service),
):
    """Returns course completion rates analysis per course."""
    return ApiResponse(data=svc.get_course_completion())
