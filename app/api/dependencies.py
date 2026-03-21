"""
FastAPI Dependency Injection bindings.
"""
import logging
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db.connection import get_session
from app.core.supabase_clients import get_supabase_anon
from app.modules.auth.auth_service import get_user_by_supabase_uid
from app.modules.auth.auth_models import User

logger = logging.getLogger(__name__)

# JWT is issued by Supabase; paste Bearer token from Streamlit session or Supabase tooling.
http_bearer = HTTPBearer(auto_error=True)

def get_db() -> Generator[Session, None, None]:
    """Yields a database session that automatically closes when the FastAPI request finishes."""
    with get_session() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    token = credentials.credentials
    """Intercepts the Bearer JWT token, validates it against Supabase Cloud, and injects the User object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials with Supabase",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        supabase = get_supabase_anon()
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not auth_response.user:
            raise credentials_exception

        supabase_uid = auth_response.user.id

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Supabase JWT validation failed: %s", type(e).__name__)
        raise credentials_exception

    user = get_user_by_supabase_uid(supabase_uid)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
        
    return user
