from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException

from app.api.dependencies import require_admin, get_notification_service
from app.api.schemas.common import ApiResponse
from app.modules.auth.models import User
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.schemas.send_request import SendBulkRequest, AddSubscriberRequest
from app.modules.notifications.schemas.notification_dto import NotificationSubscriberDTO

router = APIRouter()

@router.post("/bulk", response_model=ApiResponse[dict], summary="Bulk send to parent list")
def send_bulk(
    body: SendBulkRequest,
    background_tasks: BackgroundTasks,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    queued_count = svc.send_bulk(body.parent_ids, body.template_name, body.extra_vars, background_tasks)
    return ApiResponse(data={"queued_count": queued_count}, message=f"Queued {queued_count} notifications")

@router.get("/subscribers", response_model=ApiResponse[List[NotificationSubscriberDTO]], summary="List report subscribers")
def get_subscribers(
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    subs = svc._repo.get_all_subscribers()
    return ApiResponse(data=[NotificationSubscriberDTO.model_validate(s) for s in subs])

@router.post("/subscribers", response_model=ApiResponse[NotificationSubscriberDTO], summary="Add report subscriber")
def add_subscriber(
    body: AddSubscriberRequest,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    sub = svc._repo.add_subscriber(body.employee_id, body.report_type, body.channel)
    return ApiResponse(data=NotificationSubscriberDTO.model_validate(sub), message="Subscriber added")

@router.delete("/subscribers/{subscriber_id}", response_model=ApiResponse[str], summary="Remove subscriber")
def remove_subscriber(
    subscriber_id: int,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    success = svc._repo.remove_subscriber(subscriber_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return ApiResponse(data="Subscriber removed successfully")
