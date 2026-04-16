"""
app/modules/notifications/models/notification_log.py
───────────────────────────────────────────────────
Audit log for notifications sent or attempting to send.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class NotificationLog(SQLModel, table=True):
    __tablename__ = "notification_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: Optional[int] = Field(default=None, foreign_key="notification_templates.id")
    channel: str = Field(description="'WHATSAPP' or 'EMAIL'")
    recipient_type: str = Field(description="'PARENT' or 'EMPLOYEE'")
    recipient_id: int = Field(description="Foreign key to the recipient's main table")
    recipient_contact: str = Field(description="Phone or email at the time of send")
    subject: Optional[str] = Field(default=None)
    body: str = Field(description="Fully rendered body")
    status: str = Field(default="PENDING", description="'PENDING', 'SENT', or 'FAILED'")
    error_message: Optional[str] = Field(default=None)
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
