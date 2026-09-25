"""
app/api/routers/notifications/internal_scheduler_router.py
──────────────────────────────────────────────────────────────
Authenticated internal trigger endpoints for scheduled reports.

These endpoints replace the unreliable in-process scheduler.
Supabase pg_cron + pg_net jobs call these endpoints on a schedule.

All endpoints require the X-Internal-Trigger-Secret header matching
settings.internal_trigger_secret. Empty secret is never allowed.
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
import logfire
import zoneinfo

from app.api.dependencies import get_notification_service
from app.core.config import settings
from app.modules.notifications.schemas.report_dto import ReportDeliveryResult
from app.modules.notifications.services.notification_service import NotificationService

router = APIRouter(prefix="/internal/reports", tags=["Internal — Scheduled Reports"])

CAIRO_TZ = zoneinfo.ZoneInfo("Africa/Cairo")

_DELIVERY_SUCCESS_OUTCOMES = {"delivered", "nothing_to_send", "disabled"}
_REPORT_DELIVERY_ERROR = "ScheduledReportDeliveryError"


def _verify_internal_secret(x_internal_trigger_secret: Optional[str] = Header(default=None)) -> None:
    """Verify the internal trigger secret header.
    
    Returns 401 in ALL cases: missing header, wrong value, or unconfigured secret.
    Never returns 422.
    """
    configured_secret = settings.internal_trigger_secret
    if not configured_secret:
        logfire.error("internal_trigger_secret_not_configured")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Internal trigger secret not configured",
        )
    if x_internal_trigger_secret != configured_secret:
        logfire.error("internal_trigger_secret_mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal trigger secret",
        )


def _get_yesterday_cairo() -> date:
    """Get yesterday's date in Cairo timezone."""
    from datetime import datetime
    now_cairo = datetime.now(CAIRO_TZ).date()
    return now_cairo - timedelta(days=1)


def _scheduled_report_response(result: ReportDeliveryResult) -> JSONResponse:
    data = result.model_dump(mode="json")
    attributes = {
        "report_type": result.report_type,
        "period_start": result.period_start.isoformat(),
        "outcome": result.outcome,
        "sent": result.sent,
        "failed": result.failed,
        "skipped": result.skipped,
    }
    period = result.period_start.isoformat()
    counts = (
        f"{result.sent} sent, {result.failed} failed, {result.skipped} skipped"
    )

    if result.outcome in _DELIVERY_SUCCESS_OUTCOMES:
        logfire.info("scheduled_report_delivered", **attributes)
        messages = {
            "delivered": f"{result.report_type} delivered for {period} ({counts})",
            "nothing_to_send": (
                f"{result.report_type} had nothing new to send for {period} "
                f"({result.skipped} already claimed)"
            ),
            "disabled": f"{result.report_type} delivery is disabled for {period}",
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": data,
                "message": messages[result.outcome],
            },
        )

    logfire.error("scheduled_report_failed", **attributes, errors=result.errors)
    messages = {
        "partial": f"{result.report_type} partially delivered for {period} ({counts})",
        "failed": f"{result.report_type} delivery failed for {period} ({counts})",
        "not_configured": f"{result.report_type} is not configured",
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": data,
            "error": _REPORT_DELIVERY_ERROR,
            "message": messages[result.outcome],
        },
    )


@router.post("/daily-report/trigger", summary="Trigger daily business report")
async def trigger_daily_report(
    target_date: Optional[date] = Query(None, description="Report date (defaults to yesterday in Cairo timezone)"),
    _secret_ok: None = Depends(_verify_internal_secret),
    svc: NotificationService = Depends(get_notification_service),
):
    """Trigger the daily business report for a specific reporting period."""
    report_date = target_date or _get_yesterday_cairo()
    result = await svc.send_daily_report(target_date=report_date, force=False)
    return _scheduled_report_response(result)


@router.post("/weekly-report/trigger", summary="Trigger weekly business report")
async def trigger_weekly_report(
    target_date: Optional[date] = Query(None, description="Report date (defaults to yesterday in Cairo timezone)"),
    _secret_ok: None = Depends(_verify_internal_secret),
    svc: NotificationService = Depends(get_notification_service),
):
    """Trigger the weekly business report for a specific reporting period."""
    report_date = target_date or _get_yesterday_cairo()
    result = await svc.send_weekly_report(target_date=report_date, force=False)
    return _scheduled_report_response(result)


@router.post("/monthly-report/trigger", summary="Trigger monthly business report")
async def trigger_monthly_report(
    target_date: Optional[date] = Query(None, description="Report date (defaults to yesterday in Cairo timezone)"),
    _secret_ok: None = Depends(_verify_internal_secret),
    svc: NotificationService = Depends(get_notification_service),
):
    """Trigger the monthly business report for a specific reporting period."""
    report_date = target_date or _get_yesterday_cairo()
    result = await svc.send_monthly_report(target_date=report_date, force=False)
    return _scheduled_report_response(result)
