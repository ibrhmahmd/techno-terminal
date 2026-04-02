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
    employee_id: int
    username: str
    password: str
    role: str

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)
