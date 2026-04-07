"""
Get Supabase JWT Token for Testing

Usage:
    python scripts/get_test_jwt.py

Then enter email and password when prompted.

The script will output a valid JWT token that can be used in tests.
"""
import os
import sys
from getpass import getpass

# Add app to path so we can import Supabase client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase_clients import get_supabase_admin


def get_jwt_token(email: str, password: str) -> str:
    """
    Authenticate with Supabase and return JWT access token.
    
    Args:
        email: User email address
        password: User password
        
    Returns:
        JWT access token string
        
    Raises:
        Exception: If authentication fails
    """
    supabase = get_supabase_admin()
    
    # Sign in with email/password
    auth_response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    
    # Extract JWT from session
    access_token = auth_response.session.access_token
    
    return access_token


def main():
    """Main entry point — interactive CLI."""
    print("=" * 60)
    print("Supabase JWT Token Generator for Testing")
    print("=" * 60)
    print()
    
    # Get credentials from user
    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)
    
    password = getpass("Password: ")
    if not password:
        print("Error: Password is required")
        sys.exit(1)
    
    print()
    print("Authenticating...")
    
    try:
        token = get_jwt_token(email, password)
        
        print()
        print("=" * 60)
        print("SUCCESS! Copy this token for testing:")
        print("=" * 60)
        print()
        print(token)
        print()
        print("=" * 60)
        print("Usage in tests:")
        print("  headers = {'Authorization': f'Bearer {token}'}")
        print("=" * 60)
        
    except Exception as e:
        print()
        print(f"ERROR: Authentication failed")
        print(f"Details: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
