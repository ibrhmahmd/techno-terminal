"""
Authentication endpoint tests — Phase 1 Priority.
Validates JWT handling, role verification, and error responses.
"""
import pytest
from tests.utils.jwt_mocks import generate_expired_token


class TestAuthMe:
    """Tests for GET /api/v1/auth/me endpoint."""
    
    def test_auth_me_success_with_admin(self, client, admin_headers):
        """
        GET /auth/me with valid admin token returns 200 + user info.
        
        Expected:
        - Status: 200 OK
        - Response: {success: true, data: {email, role, id}}
        - Role: "admin"
        """
        response = client.get("/api/v1/auth/me", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["email"] == "admin@test.com"
        assert data["data"]["role"] == "admin"
    
    def test_auth_me_success_with_system_admin(self, client, system_admin_headers):
        """
        GET /auth/me with valid system_admin token returns 200 + user info.
        
        Expected:
        - Status: 200 OK
        - Role: "system_admin"
        """
        response = client.get("/api/v1/auth/me", headers=system_admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "system_admin"
    
    def test_auth_me_no_token(self, client):
        """
        GET /auth/me without token returns 401 Unauthorized.
        
        Expected:
        - Status: 401
        - Response: {success: false, error: "Unauthorized"}
        """
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Unauthorized"
    
    def test_auth_me_invalid_token_format(self, client):
        """
        GET /auth/me with malformed token returns 401.
        
        Expected:
        - Status: 401
        - No server error (graceful handling)
        """
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-format"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_auth_me_expired_token(self, client):
        """
        GET /auth/me with expired token returns 401.
        
        Expected:
        - Status: 401
        - Token expiration detected
        """
        expired_token = generate_expired_token(
            user_id="expired-user",
            role="admin",
            email="expired@test.com"
        )
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401


class TestAuthProtectedEndpoints:
    """Tests that protected endpoints reject unauthenticated requests."""
    
    def test_crm_students_requires_auth(self, client):
        """GET /crm/students without auth returns 401."""
        response = client.get("/api/v1/crm/students")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_finance_receipts_requires_auth(self, client):
        """POST /finance/receipts without auth returns 401."""
        response = client.post("/api/v1/finance/receipts", json={})
        
        assert response.status_code == 401
    
    def test_hr_employees_requires_auth(self, client):
        """GET /hr/employees without auth returns 401."""
        response = client.get("/api/v1/hr/employees")
        
        assert response.status_code == 401
    
    def test_enrollments_requires_auth(self, client):
        """POST /enrollments without auth returns 401."""
        response = client.post("/api/v1/enrollments", json={})
        
        assert response.status_code == 401
