from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_admin, get_notification_service
from app.api.schemas.common import ApiResponse
from app.modules.auth.models import User
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.schemas.template_dto import TemplateDTO, CreateTemplateRequest, UpdateTemplateRequest, TemplateTestResultDTO

router = APIRouter()

@router.get("/templates", response_model=ApiResponse[List[TemplateDTO]], summary="List all templates")
def list_templates(
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    templates = svc._repo.get_all_templates()
    return ApiResponse(data=[TemplateDTO.model_validate(t) for t in templates])

@router.get("/templates/{template_id}", response_model=ApiResponse[TemplateDTO], summary="Get single template")
def get_template(
    template_id: int,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    template = svc._repo.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ApiResponse(data=TemplateDTO.model_validate(template))

@router.post("/templates", response_model=ApiResponse[TemplateDTO], summary="Create custom template")
def create_template(
    body: CreateTemplateRequest,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    template = svc._repo.create_template(
        name=body.name,
        channel=body.channel,
        body=body.body,
        variables=body.variables,
        subject=body.subject,
        is_standard=body.is_standard
    )
    return ApiResponse(data=TemplateDTO.model_validate(template), message="Template created")

@router.put("/templates/{template_id}", response_model=ApiResponse[TemplateDTO], summary="Update template")
def update_template(
    template_id: int,
    body: UpdateTemplateRequest,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    template = svc._repo.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_standard:
        # Prevent dangerous updates to standard templates. Only allow body/subject/is_active
        kwargs = body.model_dump(exclude_unset=True)
        if "name" in kwargs or "variables" in kwargs or "channel" in kwargs:
            raise HTTPException(status_code=400, detail="Cannot edit name, channel, or variables of a standard template")
    
    updated = svc._repo.update_template(template_id, **body.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Template not found")
    return ApiResponse(data=TemplateDTO.model_validate(updated), message="Template updated")

@router.delete("/templates/{template_id}", response_model=ApiResponse[str], summary="Delete template")
def delete_template(
    template_id: int,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service)
):
    template = svc._repo.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_standard:
        raise HTTPException(status_code=400, detail="Standard templates cannot be deleted")
        
    svc._repo.delete_template(template_id)
    return ApiResponse(data="Template deleted successfully")


# ── Template Testing ────────────────────────────────────────────────────────

@router.post(
    "/templates/{template_id}/test",
    response_model=ApiResponse[TemplateTestResultDTO],
    summary="Test template rendering",
    description="Render template with placeholder values and send test email to all additional recipients."
)
def test_template(
    template_id: int,
    _user: User = Depends(require_admin),
    svc: NotificationService = Depends(get_notification_service),
):
    """
    Test a notification template by:
    1. Rendering it with placeholder values (e.g., [Student Name])
    2. Sending test email to all additional recipients
    3. Returning full render details and send status
    """
    try:
        result = svc.test_template(template_id)
        return ApiResponse(
            data=result,
            message=f"Test email would be sent to {result.recipients_sent} recipients"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
