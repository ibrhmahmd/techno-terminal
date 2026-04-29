from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationLogDTO(BaseModel):
    id: int
    template_id: Optional[int]
    channel: str
    recipient_type: str
    recipient_id: int
    recipient_contact: str
    subject: Optional[str]
    body: str
    status: str
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
