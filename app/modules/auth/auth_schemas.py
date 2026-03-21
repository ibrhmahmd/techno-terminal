"""
Request/response DTOs for auth HTTP endpoints (extend as routes are added).
Service-layer operations use shared exceptions; these are for JSON bodies only.
"""

from pydantic import BaseModel, Field

from app.shared.constants import MIN_PASSWORD_LENGTH


class PasswordResetBody(BaseModel):
    """Example body for a future admin password-reset route."""

    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)
