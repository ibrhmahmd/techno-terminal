"""
app/modules/auth/auth_schemas.py
──────────────────────────────────
Typed input DTOs for the Auth service layer.
"""
from pydantic import BaseModel


class AuthenticateInput(BaseModel):
    """Input for auth_service.authenticate()."""
    username: str
    password: str


class ChangePasswordInput(BaseModel):
    """Input for auth_service.change_password()."""
    user_id: int
    current_password: str
    new_password: str
