"""
FastAPI Dependency Injection bindings.
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from jose import JWTError, jwt

from app.db.connection import get_session
from app.modules.auth.auth_service import get_user_by_username
from app.modules.auth.auth_models import UserRead

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Match these to your environment variables
SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_ME_IN_PROD"
ALGORITHM = "HS256"

def get_db() -> Generator[Session, None, None]:
    """Yields a database session that automatically closes when the FastAPI request finishes."""
    with get_session() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    """Intercepts the Bearer JWT token, decrypts it, and injects the User object into the route."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user
