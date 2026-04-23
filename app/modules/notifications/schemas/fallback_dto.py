"""
app/modules/notifications/schemas/fallback_dto.py
────────────────────────────────────────────────
DTOs for fallback notification handling.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class FallbackAlertContext(BaseModel):
    """Context information for fallback alert notifications."""
    model_config = ConfigDict(from_attributes=True)
    
    notification_type: str
    entity_id: Optional[int] = None
    entity_description: Optional[str] = None
    intended_recipients_count: int = 0


class FallbackAlertResult(BaseModel):
    """Result of sending fallback alert."""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    message: str
    recipient_email: str
