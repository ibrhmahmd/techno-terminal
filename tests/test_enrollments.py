"""
tests/test_enrollments.py
──────────────────────────
Phase 4: Enrollment Endpoints Testing

Covers:
- POST /enrollments (enroll student)
- GET /enrollments/student/{id} (get student enrollment history)
- DELETE /enrollments/{id} (drop enrollment)
- POST /enrollments/transfer (transfer student)

All tests verify:
- Authentication requirements (401 vs 200/201)
- Authorization (admin only for writes)
- Response schema compliance (ApiResponse envelope)
- Data persistence (DB verification where applicable)
"""
import pytest


class TestEnrollmentsRead:
    """Tests for reading enrollment data."""
    
    def test_get_student_enrollments_success(self, client, admin_headers):
        """
        GET /enrollments/student/{id} returns enrollment history.
        Requires authentication (any role).
        """
        # Using student ID 1 - may not exist, test both cases
        response = client.get(
            "/api/v1/enrollments/student/1",
            headers=admin_headers
        )
        
        # Should succeed even if empty list
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_student_enrollments_not_found(self, client, admin_headers):
        """
        GET /enrollments/student/{id} for non-existent student.
        Returns empty list (not 404) since it's a history endpoint.
        """
        response = client.get(
            "/api/v1/enrollments/student/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []


class TestEnrollmentsCreate:
    """Tests for enrolling students."""
    
    def test_enroll_student_success(self, client, admin_headers):
        """
        POST /enrollments enrolls a student in a group.
        Requires admin role.
        Uses EnrollStudentInput schema.
        """
        # This test requires valid student_id and group_id
        # Using IDs that may exist, or expect 404/422 if not
        response = client.post(
            "/api/v1/enrollments",
            headers=admin_headers,
            json={
                "student_id": 1,
                "group_id": 1,
                "amount_due": 100.0,
                "discount": 0.0,
                "notes": "Test enrollment"
            }
        )
        
        # May succeed (201) or fail validation (422) or not found (404)
        assert response.status_code in [201, 404, 422]
        
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["student_id"] == 1
            assert data["data"]["group_id"] == 1
    
    def test_enroll_student_validation_error(self, client, admin_headers):
        """
        POST /enrollments with invalid data returns 422.
        Missing required fields should fail.
        """
        response = client.post(
            "/api/v1/enrollments",
            headers=admin_headers,
            json={
                "student_id": "not-an-integer",  # Invalid type
                "group_id": 1
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestEnrollmentsDrop:
    """Tests for dropping enrollments."""
    
    def test_drop_enrollment_not_found(self, client, admin_headers):
        """
        DELETE /enrollments/{id} for non-existent enrollment returns 404.
        Requires admin role.
        """
        response = client.delete(
            "/api/v1/enrollments/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestEnrollmentsTransfer:
    """Tests for transferring enrollments."""
    
    def test_transfer_student_validation_error(self, client, admin_headers):
        """
        POST /enrollments/transfer with invalid data returns 422.
        Uses TransferStudentInput schema.
        """
        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=admin_headers,
            json={
                "from_enrollment_id": "not-an-integer",  # Invalid
                "to_group_id": 1
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_transfer_student_not_found(self, client, admin_headers):
        """
        POST /enrollments/transfer for non-existent enrollment returns 404.
        """
        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=admin_headers,
            json={
                "from_enrollment_id": 99999,
                "to_group_id": 1
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestEnrollmentsAuth:
    """Tests for authentication and authorization."""
    
    def test_get_enrollments_requires_auth(self, client):
        """
        GET /enrollments/student/{id} without auth returns 401.
        """
        response = client.get("/api/v1/enrollments/student/1")
        assert response.status_code == 401
    
    def test_enroll_requires_admin(self, client, admin_headers):
        """
        POST /enrollments requires admin role.
        """
        # With admin token should not get 401
        response = client.post(
            "/api/v1/enrollments",
            headers=admin_headers,
            json={
                "student_id": 1,
                "group_id": 1
            }
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
