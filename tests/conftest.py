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
    """Generate valid admin JWT for testing."""
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
    session = get_session()
    try:
        yield session
        session.rollback()  # Clean up test data
    finally:
        session.close()
