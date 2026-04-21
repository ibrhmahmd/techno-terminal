"""
app/api/routers/notifications/admin_settings_router.py
───────────────────────────────────────────────────────────
Admin notification settings API.
Base path: /api/v1/notifications/admin
"""
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr

from app.api.dependencies import require_admin, get_current_user
from app.api.schemas import ApiResponse
from app.db.connection import get_session
from app.modules.auth.models.auth_models import User
from app.modules.notifications.schemas.admin_settings_dto import (
    AdminNotificationSettingDTO,
    AdditionalRecipientDTO,
    AdminSettingsResponse,
    UpdateAdminSettingsRequest,
    ToggleNotificationRequest,
    AddRecipientRequest,
    UpdateRecipientRequest,
)
from app.modules.notifications.repositories.admin_settings_repository import AdminSettingsRepository


router = APIRouter(prefix="/admin", tags=["Admin Notification Settings"])


# ── Dependencies ────────────────────────────────────────────────────────

def get_settings_repo():
    with get_session() as session:
        yield AdminSettingsRepository(session)


NOTIFICATION_DESCRIPTIONS = {
    "enrollment_created": "New enrollment confirmation",
    "enrollment_completed": "Enrollment completed successfully",
    "enrollment_dropped": "Student dropped from enrollment",
    "enrollment_transferred": "Student transferred between groups",
    "level_progression": "Student progressed to next level",
    "payment_received": "Payment receipt confirmation",
    "payment_reminder": "Payment due reminder",
    "daily_report": "Daily business summary report",
    "weekly_report": "Weekly business summary report",
    "monthly_report": "Monthly business summary report",
    "competition_team_registration": "Competition team registration",
    "competition_fee_payment": "Competition fee payment receipt",
    "competition_placement": "Competition placement announcement",
}


# ── Settings Endpoints ─────────────────────────────────────────────────

@router.get(
    "/settings/me",
    response_model=ApiResponse[AdminSettingsResponse],
    summary="Get my notification settings",
    description="Returns current admin's notification settings and additional recipients.",
)
def get_my_settings(
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Get current admin's notification settings."""
    # Initialize defaults if no settings exist
    settings = repo.get_admin_settings(current_user.id)
    if not settings:
        repo.initialize_default_settings(current_user.id)
        settings = repo.get_admin_settings(current_user.id)
    
    # Build response with descriptions
    settings_with_desc = [
        AdminNotificationSettingDTO(
            notification_type=s["notification_type"],
            is_enabled=s["is_enabled"],
            channel=s["channel"],
            description=NOTIFICATION_DESCRIPTIONS.get(s["notification_type"], s["notification_type"]),
        )
        for s in settings
    ]
    
    # Get additional recipients
    recipients = repo.get_additional_recipients(current_user.id)
    recipients_dto = [
        AdditionalRecipientDTO(
            id=r["id"],
            email=r["email"],
            label=r["label"],
            notification_types=r["notification_types"],
            is_active=r["is_active"],
        )
        for r in recipients
    ]
    
    return ApiResponse(
        data=AdminSettingsResponse(
            admin_id=current_user.id,
            settings=settings_with_desc,
            additional_recipients=recipients_dto,
        )
    )


@router.put(
    "/settings/me",
    response_model=ApiResponse[Dict[str, bool]],
    summary="Update my notification settings",
    description="Bulk update notification settings for current admin.",
)
def update_my_settings(
    request: UpdateAdminSettingsRequest,
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Update current admin's notification settings."""
    for notification_type, is_enabled in request.settings.items():
        repo.upsert_setting(current_user.id, notification_type, is_enabled)
    
    return ApiResponse(data=request.settings)


@router.get(
    "/settings/me/types/{notification_type}",
    response_model=ApiResponse[AdminNotificationSettingDTO],
    summary="Get specific notification setting",
)
def get_notification_setting(
    notification_type: str,
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Get specific notification type setting."""
    setting = repo.get_setting(current_user.id, notification_type)
    if not setting:
        raise HTTPException(status_code=404, detail="Notification setting not found")
    
    return ApiResponse(
        data=AdminNotificationSettingDTO(
            notification_type=setting["notification_type"],
            is_enabled=setting["is_enabled"],
            channel=setting["channel"],
            description=NOTIFICATION_DESCRIPTIONS.get(notification_type, notification_type),
        )
    )


@router.put(
    "/settings/me/types/{notification_type}",
    response_model=ApiResponse[AdminNotificationSettingDTO],
    summary="Toggle specific notification",
)
def toggle_notification(
    notification_type: str,
    request: ToggleNotificationRequest,
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Enable or disable specific notification type."""
    repo.upsert_setting(current_user.id, notification_type, request.is_enabled)
    
    return ApiResponse(
        data=AdminNotificationSettingDTO(
            notification_type=notification_type,
            is_enabled=request.is_enabled,
            channel="EMAIL",
            description=NOTIFICATION_DESCRIPTIONS.get(notification_type, notification_type),
        )
    )


# ── Additional Recipients Endpoints ────────────────────────────────────

@router.get(
    "/settings/me/additional-recipients",
    response_model=ApiResponse[List[AdditionalRecipientDTO]],
    summary="List additional recipients",
)
def list_additional_recipients(
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """List all additional email recipients for current admin."""
    recipients = repo.get_additional_recipients(current_user.id)
    return ApiResponse(
        data=[
            AdditionalRecipientDTO(
                id=r["id"],
                email=r["email"],
                label=r["label"],
                notification_types=r["notification_types"],
                is_active=r["is_active"],
            )
            for r in recipients
        ]
    )


@router.post(
    "/settings/me/additional-recipients",
    response_model=ApiResponse[AdditionalRecipientDTO],
    summary="Add additional recipient",
    status_code=201,
)
def add_additional_recipient(
    request: AddRecipientRequest,
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Add new additional email recipient."""
    recipient_id = repo.add_recipient(
        admin_id=current_user.id,
        email=request.email,
        label=request.label,
        notification_types=request.notification_types,
    )
    
    return ApiResponse(
        data=AdditionalRecipientDTO(
            id=recipient_id,
            email=request.email,
            label=request.label,
            notification_types=request.notification_types,
            is_active=True,
        )
    )


@router.put(
    "/settings/me/additional-recipients/{recipient_id}",
    response_model=ApiResponse[AdditionalRecipientDTO],
    summary="Update recipient",
)
def update_recipient(
    recipient_id: int,
    request: UpdateRecipientRequest,
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Update additional recipient settings."""
    existing = repo.get_recipient(recipient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    updated = repo.update_recipient(
        recipient_id=recipient_id,
        email=request.email,
        label=request.label,
        notification_types=request.notification_types,
        is_active=request.is_active,
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Get updated data
    recipient = repo.get_recipient(recipient_id)
    return ApiResponse(
        data=AdditionalRecipientDTO(
            id=recipient["id"],
            email=recipient["email"],
            label=recipient["label"],
            notification_types=recipient["notification_types"],
            is_active=recipient["is_active"],
        )
    )


@router.delete(
    "/settings/me/additional-recipients/{recipient_id}",
    response_model=ApiResponse[Dict[str, str]],
    summary="Remove recipient",
)
def delete_recipient(
    recipient_id: int,
    current_user: User = Depends(require_admin),
    repo: AdminSettingsRepository = Depends(get_settings_repo),
):
    """Remove additional recipient."""
    deleted = repo.delete_recipient(recipient_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    return ApiResponse(data={"message": "Recipient removed successfully"})
