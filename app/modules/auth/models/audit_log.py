from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

from app.shared.datetime_utils import utc_now


class AuditLogEventType:
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_REACTIVATED = "account_reactivated"
    USER_CREATED = "user_created"
    USER_INVITED = "user_invited"
    INVITE_COMPLETED = "invite_completed"
    EMAIL_CHANGED = "email_changed"
    ROLE_CHANGED = "role_changed"


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    event_type: str = Field(nullable=False)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
