"""
app/modules/notifications/models/notification_subscriber.py
──────────────────────────────────────────────────────────
Employees who are subscribed to various automated reports.
"""
from typing import Optional

from sqlmodel import SQLModel, Field


class NotificationSubscriber(SQLModel, table=True):
    __tablename__ = "notification_subscribers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    report_type: str = Field(description="'DAILY', 'WEEKLY', 'MONTHLY' or 'ALL'")
    channel: str = Field(description="'EMAIL' or 'WHATSAPP'")
    is_active: bool = Field(default=True)
