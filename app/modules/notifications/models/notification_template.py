"""
app/modules/notifications/models/notification_template.py
────────────────────────────────────────────────────────
Template for notifications.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import SQLModel, Field


class NotificationTemplate(SQLModel, table=True):
    __tablename__ = "notification_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, description="Internal identifier for the template, e.g., 'absence_alert'")
    channel: str = Field(description="'WHATSAPP' or 'EMAIL'")
    subject: Optional[str] = Field(default=None, description="Email subject, ignored for WhatsApp")
    body: str = Field(description="Body of the notification, with {{variable}} placeholders")
    variables: list[str] = Field(
        sa_column=Column(ARRAY(String), nullable=False),
        description="List of variables expected in the template, e.g., ['student_name']"
    )
    is_standard: bool = Field(default=False, description="Cannot be deleted if standard")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
