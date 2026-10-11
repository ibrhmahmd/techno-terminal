from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.deps import require_admin
from app.modules.notifications.api.deps import get_report_service
from app.api.schemas.common import ApiResponse
from app.modules.auth.models import User
from app.modules.notifications.services.report_notifications import ReportNotificationService
from app.modules.notifications.schemas.send_request import SendBulkRequest
from app.modules.notifications.schemas.notification_dto import BulkSendResultDTO

router = APIRouter()

@router.post("/bulk", response_model=ApiResponse[BulkSendResultDTO], summary="Bulk send to parent list")
def send_bulk(
    body: SendBulkRequest,
    background_tasks: BackgroundTasks,
    _user: User = Depends(require_admin),
    svc: ReportNotificationService = Depends(get_report_service)
):
    queued_count = svc.send_bulk(body.parent_ids, body.template_name, body.extra_vars, background_tasks)
    return ApiResponse(data=BulkSendResultDTO(queued_count=queued_count), message=f"Queued {queued_count} notifications")
