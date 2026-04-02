"""
Mock Supabase JWT generation for tests.
Uses HS256 with a test secret (never use in production).
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional

TEST_SECRET = "test-secret-for-local-testing-only-never-use-in-prod"


def generate_mock_supabase_token(
    user_id: str,
    role: str,
    email: str,
    expires_in_minutes: int = 30
) -> str:
    """
    Generate a mock Supabase-style JWT for testing.
    
    Mimics the structure of Supabase auth tokens:
    {
        "sub": "user-uuid",
        "role": "authenticated",
        "app_metadata": {"role": "admin"},
        "email": "user@example.com",
        "iat": 1234567890,
        "exp": 1234567890
    }
    
    Args:
        user_id: Unique user identifier (maps to users.supabase_uid)
        role: User role (admin, system_admin)
        email: User email address
        expires_in_minutes: Token expiration time
        
    Returns:
        Valid JWT token string
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "app_metadata": {"role": role},
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=expires_in_minutes)
    }
    
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def decode_mock_token(token: str) -> dict:
    """
    Decode a mock token for verification in tests.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
    """
    return jwt.decode(token, TEST_SECRET, algorithms=["HS256"])


def generate_expired_token(user_id: str, role: str, email: str) -> str:
    """Generate an expired token for testing 401 responses."""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "app_metadata": {"role": role},
        "email": email,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1)  # Expired 1 hour ago
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")
