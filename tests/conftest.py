"""
Test configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import create_app
from tests.utils.jwt_mocks import generate_mock_supabase_token


@pytest.fixture(scope="session")
def app():
    """FastAPI application instance."""
    return create_app()


@pytest.fixture(scope="function")
def client(app):
    """FastAPI TestClient instance — fresh for each test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    """
    Real Supabase JWT token for testing.
    
    Generated via: python scripts/get_test_jwt.py
    User: mrs.shimaa@system.local
    
    Note: Token expires after ~1 hour. Regenerate with script when needed.
    """
    # Real token from scripts/get_test_jwt.py
    return "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRmN2U4ODliLWNkNWItNDZlOS1hZDc1LWI4ZDMyY2I3YzI4NCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3NyYnBwa2N2cmdpb25laXRrdGRqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2YzY5OWEwOS0zNTViLTQyY2UtOGE5YS1iNmJmODNlZDhhMDMiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc1MTMyMDE5LCJpYXQiOjE3NzUxMjg0MTksImVtYWlsIjoibXJzLnNoaW1hYUBzeXN0ZW0ubG9jYWwiLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3NTEyODQxOX1dLCJzZXNzaW9uX2lkIjoiOWRmMGM1YTYtYmUyMy00YmFlLWI3YmQtN2M5ODljMmRhNjk3IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.fgsMI2KGkfyr0idBP2pULPOOwKQ723UTO749Wh08QweITaAgaLWof1C5b6TpayjmyyS_6RinNei-HYOYhJTI9Q"
@pytest.fixture
def system_admin_token():
    """Generate valid system_admin JWT for testing."""
    return generate_mock_supabase_token(
        user_id="test-sysadmin-001",
        role="system_admin",
        email="sysadmin@test.com"
    )


@pytest.fixture
def admin_headers(admin_token):
    """Auth headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def system_admin_headers(system_admin_token):
    """Auth headers with system_admin token."""
    return {"Authorization": f"Bearer {system_admin_token}"}


@pytest.fixture
def db_session():
    """
    Database session for test data setup.
    Uses transaction rollback for test isolation.
    """
    from app.db.connection import get_session
    
    with get_session() as session:
        yield session
        # Rollback happens automatically on exception
        # Or we can explicitly rollback here for cleanup
