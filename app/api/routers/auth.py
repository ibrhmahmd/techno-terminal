"""
app/api/routers/auth.py
────────────────────────
Authentication endpoints.

Prefix: /api/v1/auth  (mounted in main.py)
Tag:    Authentication

Phase 0 (done): GET /me — identity check for any valid JWT.
Phase 1 (done): Role enforcement via require_admin / require_any in dependencies.py.

All tokens are issued by Supabase. Use "Authorize" in Swagger UI with:
    Bearer <your_supabase_access_token>
"""
from fastapi import APIRouter, Depends

from app.modules.auth import User, UserPublic
from app.api.dependencies import get_current_user, require_admin

router = APIRouter()


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current authenticated user",
    description=(
        "Returns the local user record mapped to the bearer JWT. "
        "Use this to verify a token is valid and retrieve your role."
    ),
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the mapped local user for a valid Supabase JWT.
    Obtain tokens via Streamlit login or Supabase Auth tooling.
    """
    return UserPublic.model_validate(current_user, from_attributes=True)
