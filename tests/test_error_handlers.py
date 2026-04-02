"""
Error handler tests — Phase 2.
Verify standardized error response format across all error types.
"""
import pytest


class TestErrorResponseStructure:
    """Verify standardized error format across all error types."""
    
    def test_401_missing_token(self, client):
        """
        GET /crm/students without token returns standard 401.
        
        Expected:
        - Status: 401
        - Response: {success: false, error: "Unauthorized", message: "..."}
        """
        response = client.get("/api/v1/crm/students")
        
        assert response.status_code == 401
        data = response.json()
        assert "success" in data
        assert "error" in data
        assert "message" in data
        assert data["success"] is False
        assert data["error"] == "Unauthorized"
    
    def test_401_invalid_token_format(self, client):
        """
        Invalid token format returns standard 401.
        
        Expected: Same structure as missing token.
        """
        response = client.get(
            "/api/v1/crm/students",
            headers={"Authorization": "Bearer invalid-token-format"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    def test_404_not_found(self, client, admin_headers):
        """
        GET /crm/students/99999 returns standard 404.
        
        Expected:
        - Status: 404
        - Response: {success: false, error: "NotFound", message: "..."}
        """
        response = client.get(
            "/api/v1/crm/students/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFound"
        assert "message" in data
    
    def test_422_validation_error(self, client, admin_headers):
        """
        POST /crm/students with invalid data returns 422.
        
        Expected:
        - Status: 422
        - Response: {success: false, error: "ValidationError", details: [...]}
        """
        response = client.post(
            "/api/v1/crm/students",
            headers=admin_headers,
            json={"full_name": ""}  # Missing required fields
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_405_method_not_allowed(self, client, admin_headers):
        """
        DELETE on GET-only endpoint returns 405.
        
        Expected: Proper error envelope even for method errors.
        """
        response = client.delete(
            "/api/v1/crm/students",
            headers=admin_headers
        )
        
        # May be 405 or 404 depending on router setup
        assert response.status_code in [405, 404]
        data = response.json()
        assert "success" in data
        assert data["success"] is False


class TestErrorFieldConsistency:
    """Ensure all error responses have consistent field structure."""
    
    def test_all_errors_have_success_field(self, client):
        """Every error response must have 'success' field set to false."""
        test_cases = [
            ("/api/v1/crm/students", None),  # 401
            ("/api/v1/crm/students/99999", {"Authorization": "Bearer invalid"}),  # 401 or 404
        ]
        
        for path, headers in test_cases:
            response = client.get(path, headers=headers or {})
            data = response.json()
            assert "success" in data, f"Missing 'success' field for {path}"
            assert data["success"] is False, f"'success' should be False for {path}"
    
    def test_all_errors_have_error_field(self, client):
        """Every error response must have 'error' field with string value."""
        response = client.get("/api/v1/crm/students")
        data = response.json()
        
        assert "error" in data
        assert isinstance(data["error"], str)
        assert len(data["error"]) > 0
    
    def test_all_errors_have_message_field(self, client):
        """Every error response must have 'message' field with string value."""
        response = client.get("/api/v1/crm/students")
        data = response.json()
        
        assert "message" in data
        assert isinstance(data["message"], str)


class TestProtectedEndpointsAuthErrors:
    """Verify all protected endpoints return 401 without auth."""
    
    def test_crm_endpoints_require_auth(self, client):
        """CRM endpoints return 401."""
        endpoints = [
            "GET /api/v1/crm/students",
            "GET /api/v1/crm/parents",
        ]
        
        for endpoint in endpoints:
            method, path = endpoint.split(" ")
            response = getattr(client, method.lower())(path)
            assert response.status_code == 401, f"{endpoint} should require auth"
    
    def test_finance_endpoints_require_auth(self, client):
        """Finance endpoints return 401."""
        response = client.get("/api/v1/finance/receipts")
        assert response.status_code == 401
    
    def test_hr_endpoints_require_auth(self, client):
        """HR endpoints return 401."""
        response = client.get("/api/v1/hr/employees")
        assert response.status_code == 401
    
    def test_enrollment_endpoints_require_auth(self, client):
        """Enrollment endpoints return 401."""
        # Use GET /enrollments/student/{id} which requires auth
        response = client.get("/api/v1/enrollments/student/1")
        assert response.status_code == 401
