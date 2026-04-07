"""
Request/response DTOs for auth HTTP endpoints (extend as routes are added).
Service-layer operations use shared exceptions; these are for JSON bodies only.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from app.shared.constants import MIN_PASSWORD_LENGTH
from app.modules.auth.models.auth_models import UserBase

class PasswordResetBody(BaseModel):
    """Example body for a future admin password-reset route."""
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)

class UserCreate(UserBase):
    """DTO for creating a local user; supabase_uid is filled after Supabase admin signup."""
    supabase_uid: Optional[str] = None

class UserRead(UserBase):
    """Safe network-facing response."""
    id: int
    supabase_uid: str
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

class UserPublic(SQLModel):
    """API / client-facing user shape (no Supabase linkage id)."""
    id: int
    username: str
    role: str
    is_active: bool = True
    employee_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
