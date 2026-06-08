import asyncio
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query

from app.api.dependencies import require_admin, get_notification_service
from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.notifications.report_request import DailyReportRequest, WeeklyReportRequest, MonthlyReportRequest
from app.modules.auth.models import User
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.schemas.send_request import SendAbsenceRequest
from app.modules.notifications.schemas.notification_dto import NotificationLogDTO
from app.modules.notifications.schemas.report_dto import DailyReportAggregateDTO

router = APIRouter()

@router.post("/absence", response_model=ApiResponse[str], summary="Trigger absence alert")
def send_absence_alert(
    body: SendAbsenceRequest,
    background_tasks: BackgroundTasks,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    svc.notify_absence(body.student_id, body.session_name, body.session_date, background_tasks)
    return ApiResponse(data="Absence notification queued")

@router.post("/receipt/{receipt_id}", response_model=ApiResponse[str], summary="Send receipt notification")
def send_receipt_notification(
    receipt_id: int,
    student_id: int,
    amount: str,
    receipt_number: str,
    background_tasks: BackgroundTasks,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    svc.payment.notify_payment_received(receipt_id, student_id, amount, receipt_number, background_tasks)
    return ApiResponse(data="Payment receipt notification queued")

@router.get("/logs", response_model=PaginatedResponse[NotificationLogDTO], summary="Get notification logs")
def get_logs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    recipient_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    template_id: Optional[int] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    # Convert date to datetime if provided
    from datetime import datetime, time
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None

    logs = svc.get_logs(
        limit=limit,
        offset=offset,
        status=status,
        channel=channel,
        search=search,
        recipient_type=recipient_type,
        start_date=start_dt,
        end_date=end_dt,
        template_id=template_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total = svc.count_logs(
        status=status,
        channel=channel,
        search=search,
        recipient_type=recipient_type,
        start_date=start_dt,
        end_date=end_dt,
        template_id=template_id
    )
    return PaginatedResponse(
        data=[NotificationLogDTO.model_validate(log) for log in logs],
        total=total,
        skip=offset,
        limit=limit
    )

@router.get("/logs/parent/{parent_id}", response_model=ApiResponse[List[NotificationLogDTO]], summary="Get parent logs")
def get_parent_logs(
    parent_id: int,
    limit: int = 50,
    offset: int = 0,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    logs = svc.get_logs(recipient_type="PARENT", recipient_id=parent_id, limit=limit, offset=offset)
    return ApiResponse(data=[NotificationLogDTO.model_validate(log) for log in logs])

@router.post("/reports/daily", response_model=ApiResponse, summary="Trigger daily report")
async def trigger_daily_report(
    body: Optional[DailyReportRequest] = None,
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
    if report_date > date.today():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report date cannot be in the future")
    svc_report = svc.report

    if body and body.email_recipients:
        attachments, variables, template = await asyncio.to_thread(
            svc_report.get_report_assets, report_date
        )
        for email in body.email_recipients:
            asyncio.create_task(
                svc_report._dispatch(template, "EMAIL", "EMPLOYEE", 0, email, variables, attachments=attachments)
            )
        return ApiResponse(data=f"Daily report queued for {len(body.email_recipients)} recipient(s)")

    try:
        date_str, pdf_b64 = await asyncio.to_thread(
            svc_report.get_daily_report_pdf_base64, report_date
        )
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {report_date}",
        )

    return ApiResponse(data={"date": date_str, "pdf_base64": pdf_b64})


@router.get("/reports/daily/data", response_model=ApiResponse, summary="Get daily report data as JSON")
async def get_daily_report_data(
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
    if report_date > date.today():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report date cannot be in the future")
    try:
        aggregates = await asyncio.to_thread(svc.report.get_daily_report_data, report_date)
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {report_date}",
        )
    return ApiResponse(data=aggregates.model_dump())


@router.post("/reports/weekly", response_model=ApiResponse, summary="Trigger weekly report")
async def trigger_weekly_report(
    body: Optional[WeeklyReportRequest] = None,
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
    if report_date > date.today():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report date cannot be in the future")
    
    # We trigger the standard dispatch. Weekly report uses email only.
    await svc.report.send_weekly_report(target_date=report_date)
    return ApiResponse(data="Weekly report email queued successfully.")


@router.get("/reports/weekly/data", response_model=ApiResponse, summary="Get weekly report data as JSON")
async def get_weekly_report_data(
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
    if report_date > date.today():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report date cannot be in the future")
    try:
        from datetime import timedelta
        week_start = report_date - timedelta(days=report_date.weekday())
        aggregates = await asyncio.to_thread(svc.report._fetch_weekly_aggregates, week_start, report_date)
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {report_date}",
        )
    return ApiResponse(data=aggregates.model_dump())


@router.post("/reports/monthly", response_model=ApiResponse, summary="Trigger monthly report")
async def trigger_monthly_report(
    body: Optional[MonthlyReportRequest] = None,
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
    if report_date > date.today():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report date cannot be in the future")
    
    await svc.report.send_monthly_report(target_date=report_date)
    return ApiResponse(data="Monthly report email queued successfully.")


@router.get("/reports/monthly/data", response_model=ApiResponse, summary="Get monthly report data as JSON")
async def get_monthly_report_data(
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
    if report_date > date.today():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report date cannot be in the future")
    try:
        month_start = report_date.replace(day=1)
        aggregates = await asyncio.to_thread(svc.report._fetch_monthly_aggregates, month_start, report_date)
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {report_date}",
        )
    return ApiResponse(data=aggregates.model_dump())
