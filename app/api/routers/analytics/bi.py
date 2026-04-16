"""
app/api/routers/analytics/bi.py
─────────────────────────────────
Business Intelligence (BI) analytics router.

Endpoints for BI metrics: trends, retention, performance, risk analysis.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, ErrorResponse
from app.modules.analytics.schemas.bi_schemas import (
    EnrollmentTrendDTO,
    RetentionMetricsDTO,
    InstructorPerformanceDTO,
    LevelRetentionFunnelDTO,
    InstructorValueMatrixDTO,
    ScheduleUtilizationDTO,
    FlightRiskStudentDTO,
    RetentionCohortDTO,
)
from app.api.dependencies import require_admin, get_bi_analytics_service
from app.modules.auth import User
from app.modules.analytics.services.bi_service import BIAnalyticsService

router = APIRouter(
    tags=["Analytics — BI"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
    }
)


@router.get(
    "/analytics/bi/enrollment-trend",
    response_model=ApiResponse[list[EnrollmentTrendDTO]],
    summary="Get enrollment trend over time",
)
def get_enrollment_trend(
    cutoff: Optional[date] = Query(None, description="Start date for trend (default: 90 days ago)"),
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns daily new enrollment counts over time."""
    return ApiResponse(data=svc.get_new_enrollments_trend(cutoff))


@router.get(
    "/analytics/bi/retention",
    response_model=ApiResponse[list[RetentionMetricsDTO]],
    summary="Get retention metrics by course",
)
def get_retention_metrics(
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns enrollment retention/dropout rates per course."""
    return ApiResponse(data=svc.get_retention_metrics())


@router.get(
    "/analytics/bi/instructor-performance",
    response_model=ApiResponse[list[InstructorPerformanceDTO]],
    summary="Get instructor performance metrics",
)
def get_instructor_performance(
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns group/student counts per instructor."""
    return ApiResponse(data=svc.get_instructor_performance())


@router.get(
    "/analytics/bi/retention-funnel",
    response_model=ApiResponse[list[LevelRetentionFunnelDTO]],
    summary="Get level retention funnel",
)
def get_level_retention_funnel(
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns student counts per course/level showing progression funnel."""
    return ApiResponse(data=svc.get_level_retention_funnel())


@router.get(
    "/analytics/bi/instructor-value",
    response_model=ApiResponse[list[InstructorValueMatrixDTO]],
    summary="Get instructor value matrix",
)
def get_instructor_value_matrix(
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns revenue and attendance correlation per instructor."""
    return ApiResponse(data=svc.get_instructor_value_matrix())


@router.get(
    "/analytics/bi/schedule-utilization",
    response_model=ApiResponse[list[ScheduleUtilizationDTO]],
    summary="Get schedule utilization",
)
def get_schedule_utilization(
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns schedule slot utilization percentages."""
    return ApiResponse(data=svc.get_schedule_utilization())


@router.get(
    "/analytics/bi/flight-risk",
    response_model=ApiResponse[list[FlightRiskStudentDTO]],
    summary="Get flight-risk students",
)
def get_flight_risk_students(
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns students likely to drop out based on attendance/debt patterns."""
    return ApiResponse(data=svc.get_flight_risk_students())



@router.get(
    "/analytics/bi/retention-analysis",
    response_model=ApiResponse[list[RetentionCohortDTO]],
    summary="Get cohort-based retention analysis",
)
def get_retention_analysis(
    months: int = Query(6, ge=1, le=12, description="Number of months for cohort analysis"),
    _user: User = Depends(require_admin),
    svc: BIAnalyticsService = Depends(get_bi_analytics_service),
):
    """Returns cohort-based retention analysis showing student retention over time."""
    return ApiResponse(data=svc.get_retention_cohorts(months))
