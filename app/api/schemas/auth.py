"""
app/api/schemas/auth.py
───────────────────────
Request/Response DTOs specifically for the Authentication HTTP router.
"""
from pydantic import BaseModel, Field

from app.modules.auth import UserPublic
from app.shared.constants import MIN_PASSWORD_LENGTH

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic

class RefreshRequest(BaseModel):
    refresh_token: str

class CreateUserRequest(BaseModel):
    employee_id: int | None = None
    username: str
    password: str
    role: str

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=1)

class UpdateProfileRequest(BaseModel):
    username: str | None = None
    email: str | None = None

class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None

class InviteUserRequest(BaseModel):
    email: str
    role: str
    employee_id: int | None = None

class RegisterUserRequest(BaseModel):
    token: str
    username: str
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)


