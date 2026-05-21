"""
Request/response DTOs for auth HTTP endpoints (extend as routes are added).
Service-layer operations use shared exceptions; these are for JSON bodies only.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import SQLModel

from app.modules.auth.models.auth_models import UserBase
from app.shared.constants import MIN_PASSWORD_LENGTH

class UserCreate(UserBase):
    """DTO for creating a local user; supabase_uid is filled after Supabase admin signup."""
    supabase_uid: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserPublic(SQLModel):
    """API / client-facing user shape (no Supabase linkage id)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool = True
    employee_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

class ChangePasswordInput(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _validate_new_password_length(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        return v

class ForgotPasswordInput(BaseModel):
    email: str

class UpdateProfileInput(BaseModel):
    username: Optional[str] = None

class UpdateUserInput(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserAdminDTO(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    supabase_uid: str
    role: str
    is_active: bool = True
    employee_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

class InviteResultDTO(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool = False
    invite_expires_at: Optional[datetime] = None

class RegisterUserInput(BaseModel):
    token: str
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def _validate_password_length(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        return v

class AuditLogEntryDTO(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    event_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

class UserSessionDTO(BaseModel):
    id: str
    created_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
