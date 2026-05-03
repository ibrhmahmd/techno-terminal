from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.dependencies import require_admin, get_notification_service
from app.api.schemas.common import ApiResponse
from app.modules.auth.models import User
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.schemas.send_request import SendBulkRequest

router = APIRouter()

@router.post("/bulk", response_model=ApiResponse[dict], summary="Bulk send to parent list") #TODO remove Dict and write a typed DTO class
def send_bulk(
    body: SendBulkRequest,
    background_tasks: BackgroundTasks,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    queued_count = svc.send_bulk(body.parent_ids, body.template_name, body.extra_vars, background_tasks)
    return ApiResponse(data={"queued_count": queued_count}, message=f"Queued {queued_count} notifications")
