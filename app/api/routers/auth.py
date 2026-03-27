from fastapi import APIRouter, Depends
from app.modules.auth import User, UserPublic
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the mapped local user for a valid Supabase JWT (Authorization: Bearer <token>).
    Obtain tokens via Streamlit login or Supabase Auth; use "Authorize" in Swagger with Bearer scheme.
    """
    return UserPublic.model_validate(current_user, from_attributes=True)
