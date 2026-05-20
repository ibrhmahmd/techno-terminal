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
    User: ibrahim.net@techno.crm
    
    Note: Token expires after ~1 hour. Regenerate with script when needed.
    """
    return "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRmN2U4ODliLWNkNWItNDZlOS1hZDc1LWI4ZDMyY2I3YzI4NCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3NyYnBwa2N2cmdpb25laXRrdGRqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxNDAwNmNlMy1lZWU0LTQzODQtYjlhOC02MDIwMDJmNmU0ODgiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc5Mjc4ODQ3LCJpYXQiOjE3NzkyNzUyNDcsImVtYWlsIjoiaWJyYWhpbS5uZXRAdGVjaG5vLmNybSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzc5Mjc1MjQ3fV0sInNlc3Npb25faWQiOiI1OGEwZWJkYS0yMmNkLTRlZWItYWRlMi00MGRiNDUxN2MzYWQiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.8lR2USPVUXv2-y2uKIX8jSyHEtS2yqhrJQy81IHk7jffzipJhDk_Ban7q81A_3rGNaY0cps9N5ZDiu8OjkmoGw"


@pytest.fixture
def mock_admin_token():
    """Generate valid admin mock JWT for testing (bypasses Supabase auth)."""
    return generate_mock_supabase_token(
        user_id="test-admin-001",
        role="admin",
        email="admin@test.com"
    )


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
def mock_admin_headers(mock_admin_token):
    """Auth headers with mock admin token."""
    return {"Authorization": f"Bearer {mock_admin_token}"}


@pytest.fixture
def system_admin_headers(system_admin_token):
    """Auth headers with system_admin token."""
    return {"Authorization": f"Bearer {system_admin_token}"}


@pytest.fixture
def override_auth(app):
    """
    Override the get_current_user dependency to bypass real Supabase JWT validation.
    
    Use this fixture in tests that don't need real Supabase auth.
    Combine with mock_admin_headers or system_admin_headers for token-passing tests.
    """
    from app.api.dependencies import get_current_user
    from app.modules.auth.models.auth_models import User

    mock_user = User(
        id=1,
        username="test_admin",
        role="admin",
        supabase_uid="test-admin-001",
        is_active=True,
    )

    async def _mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_system_admin_auth(app):
    """
    Override get_current_user with a system_admin user.
    Use with system_admin_headers for token-passing tests.
    """
    from app.api.dependencies import get_current_user
    from app.modules.auth.models.auth_models import User

    mock_user = User(
        id=1,
        username="test_sysadmin",
        role="system_admin",
        supabase_uid="test-sysadmin-001",
        is_active=True,
    )

    async def _mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


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
