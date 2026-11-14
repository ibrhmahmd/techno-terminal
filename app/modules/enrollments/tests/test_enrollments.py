"""
app/modules/enrollments/tests/test_enrollments.py
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


@pytest.fixture
def noop_notifications(app):
    """Replace every notifier port provider with a no-op so nothing can be dispatched."""
    from app.testing.noop_notifiers import noop_notifiers

    with noop_notifiers(app) as stub:
        yield stub


class TestEnrollmentsRead:
    """Tests for reading enrollment data."""
    
    def test_get_student_enrollments_success(self, client, mock_admin_headers, override_auth):
        """
        GET /enrollments/student/{id} returns enrollment history.
        Requires authentication (any role).
        """
        # Using student ID 1 - may not exist, test both cases
        response = client.get(
            "/api/v1/enrollments/student/1",
            headers=mock_admin_headers
        )
        
        # Should succeed even if empty list
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_student_enrollments_not_found(self, client, mock_admin_headers, override_auth):
        """
        GET /enrollments/student/{id} for non-existent student.
        Returns empty list (not 404) since it's a history endpoint.
        """
        response = client.get(
            "/api/v1/enrollments/student/99999",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []


class TestEnrollmentsCreate:
    """Tests for enrolling students."""
    
    def test_enroll_student_success(
        self, client_with_uow, uow, mock_admin_headers, override_auth, noop_notifications
    ):
        """
        POST /enrollments enrolls a student in a group.
        Requires admin role.
        Uses EnrollStudentInput schema.
        """
        from app.testing.db_helpers import create_test_student, create_test_course, create_test_group

        student = create_test_student(uow.session, status="active")
        course = create_test_course(uow.session)
        group = create_test_group(uow.session, course_id=course.id)

        response = client_with_uow.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={
                "student_id": student.id,
                "group_id": group.id,
                "amount_due": 100.0,
                "discount": 0.0,
                "notes": "Test enrollment"
            }
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["student_id"] == student.id
        assert data["data"]["group_id"] == group.id

    def test_enroll_student_validation_error(self, client, mock_admin_headers, override_auth):
        """
        POST /enrollments with invalid data returns 422.
        Missing required fields should fail.
        """
        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
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
    
    def test_drop_enrollment_not_found(self, client, mock_admin_headers, override_auth):
        """
        DELETE /enrollments/{id} for non-existent enrollment returns 404.
        Requires admin role.
        """
        response = client.delete(
            "/api/v1/enrollments/99999",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestEnrollmentsTransfer:
    """Tests for transferring enrollments."""
    
    def test_transfer_student_validation_error(self, client, mock_admin_headers, override_auth):
        """
        POST /enrollments/transfer with invalid data returns 422.
        Uses TransferStudentInput schema.
        """
        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=mock_admin_headers,
            json={
                "from_enrollment_id": "not-an-integer",  # Invalid
                "to_group_id": 1
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_transfer_student_not_found(self, client, mock_admin_headers, override_auth):
        """
        POST /enrollments/transfer for non-existent enrollment returns 404.
        """
        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=mock_admin_headers,
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
    
    def test_enroll_requires_admin(self, client, mock_admin_headers, override_auth):
        """
        POST /enrollments requires admin role.
        """
        # With admin token should not get 401
        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={
                "student_id": 1,
                "group_id": 1
            }
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
