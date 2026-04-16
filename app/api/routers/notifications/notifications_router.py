from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.dependencies import require_admin, get_notification_service
from app.api.schemas.common import ApiResponse
from app.modules.auth.models import User
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.schemas.send_request import SendAbsenceRequest
from app.modules.notifications.schemas.notification_dto import NotificationLogDTO

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
