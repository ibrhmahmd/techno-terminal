"""
app/modules/notifications/schemas/admin_settings_dto.py
───────────────────────────────────────────────────────
DTOs for admin notification settings API.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr

from app.modules.notifications.constants import NotificationType


class AdminNotificationSettingDTO(BaseModel):
    """Single notification setting for an admin."""
    notification_type: str
    is_enabled: bool
    channel: str  # 'EMAIL' currently
    description: str  # Human-readable description


class AdditionalRecipientDTO(BaseModel):
    """Additional email recipient (non-admin)."""
    id: int
    email: str
    label: Optional[str]
    notification_types: Optional[List[str]]  # null = all notifications
    is_active: bool


class AdminSettingsResponse(BaseModel):
    """Complete settings for an admin."""
    admin_id: int
    settings: List[AdminNotificationSettingDTO]
    additional_recipients: List[AdditionalRecipientDTO]


class UpdateAdminSettingsRequest(BaseModel):
    """Bulk update settings."""
    settings: Dict[NotificationType, bool]  # notification_type -> is_enabled #TODO remove Dict and write a typed DTO class


class ToggleNotificationRequest(BaseModel):
    """Toggle single notification type."""
    is_enabled: bool


class AddRecipientRequest(BaseModel):
    """Add new additional recipient."""
    email: EmailStr
    label: Optional[str] = None
    notification_types: Optional[List[NotificationType]] = None  # null = all


class UpdateRecipientRequest(BaseModel):
    """Update existing recipient."""
    email: Optional[EmailStr] = None
    label: Optional[str] = None
    notification_types: Optional[List[NotificationType]] = None
    is_active: Optional[bool] = None
