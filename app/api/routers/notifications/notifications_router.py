import asyncio
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query

from app.api.dependencies import require_admin, get_notification_service
from app.api.schemas.common import ApiResponse
from app.api.schemas.notifications.report_request import DailyReportRequest
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
    svc.notify_payment_receipt(receipt_id, student_id, amount, receipt_number, background_tasks)
    return ApiResponse(data="Payment receipt notification queued")

@router.get("/logs", response_model=ApiResponse[List[NotificationLogDTO]], summary="Get notification logs")
def get_logs(
    limit: int = 50,
    offset: int = 0,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    logs = svc._repo.get_logs(limit=limit, offset=offset)
    return ApiResponse(data=[NotificationLogDTO.model_validate(log) for log in logs])

@router.get("/logs/parent/{parent_id}", response_model=ApiResponse[List[NotificationLogDTO]], summary="Get parent logs")
def get_parent_logs(
    parent_id: int,
    limit: int = 50,
    offset: int = 0,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    logs = svc._repo.get_logs(recipient_type="PARENT", recipient_id=parent_id, limit=limit, offset=offset)
    return ApiResponse(data=[NotificationLogDTO.model_validate(log) for log in logs])

@router.post("/reports/daily", response_model=ApiResponse, summary="Trigger daily report")
async def trigger_daily_report(
    body: Optional[DailyReportRequest] = None,
    target_date: Optional[date] = Query(None, description="Report date (ISO format, defaults to today)"),
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    report_date = target_date or date.today()
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
    try:
        aggregates = await asyncio.to_thread(svc.report.get_daily_report_data, report_date)
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {report_date}",
        )
    return ApiResponse(data=aggregates.model_dump())
