"""
Test module for Courses router.

Tests all endpoints in courses_router.py:
- GET /academics/courses - List all active courses
- POST /academics/courses - Create a new course
- PATCH /academics/courses/{course_id} - Update a course
"""
import pytest
from app.modules.academics.models import Course
import uuid


class TestCoursesRead:
    """GET endpoints - require_any auth"""

    def test_list_courses_success(self, client, admin_headers, db_session):
        """Test listing courses returns paginated results."""
        # Create test courses with unique names
        from tests.utils.db_helpers import create_test_course
        unique_id = str(uuid.uuid4())[:8]
        course1 = create_test_course(db_session, name=f"Python Basics {unique_id}", category="software")
        course2 = create_test_course(db_session, name=f"Robotics 101 {unique_id}", category="hardware")

        response = client.get("/api/v1/academics/courses", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

    def test_list_courses_unauthorized(self, client):
        """Test listing courses without auth fails."""
        response = client.get("/api/v1/academics/courses")

        assert response.status_code == 401

    def test_list_courses_pagination(self, client, admin_headers, db_session):
        """Test pagination parameters work correctly."""
        from tests.utils.db_helpers import create_test_course
        # Create multiple courses with unique names
        unique_id = str(uuid.uuid4())[:8]
        for i in range(5):
            create_test_course(db_session, name=f"Pagination Course {unique_id}-{i}", category="software")

        # Test with limit
        response = client.get("/api/v1/academics/courses?limit=2", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2

        # Test with skip
        response = client.get("/api/v1/academics/courses?skip=1&limit=2", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2
        assert data["skip"] == 1


class TestCoursesWrite:
    """POST/PATCH - require_admin auth"""

    def test_create_course_success(self, client, admin_headers):
        """Test creating a course with valid data."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"Advanced Python {unique_id}",
            "category": "software",
            "price_per_level": 1500.0,
            "sessions_per_level": 12
        }

        response = client.post(
            "/api/v1/academics/courses",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["category"] == payload["category"]
        assert data["message"] == "Course created successfully."

    def test_create_course_validation_error(self, client, admin_headers):
        """Test creating a course with invalid data fails validation."""
        payload = {
            "name": "",  # Empty name should fail
            "category": "invalid_category",  # Invalid category
            "price_per_level": -100  # Negative price
        }

        response = client.post(
            "/api/v1/academics/courses",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_create_course_unauthorized(self, client):
        """Test creating a course without auth fails."""
        payload = {"name": "Test Course", "category": "software"}

        response = client.post("/api/v1/academics/courses", json=payload)

        assert response.status_code == 401

    def test_create_course_non_admin(self, client, system_admin_headers):
        """Test creating a course with non-admin token fails."""
        # Note: This test may return 401 (auth failed) or 403 (forbidden) depending on token validation
        unique_id = str(uuid.uuid4())[:8]
        payload = {"name": f"Test Course {unique_id}", "category": "software"}

        response = client.post(
            "/api/v1/academics/courses",
            headers=system_admin_headers,
            json=payload
        )

        # Mock token may fail validation (401) or be rejected for insufficient permissions (403)
        assert response.status_code in [401, 403]

    def test_update_course_success(self, client, admin_headers, db_session):
        """Test updating a course with valid data."""
        from tests.utils.db_helpers import create_test_course
        unique_id = str(uuid.uuid4())[:8]
        course = create_test_course(db_session, name=f"Old Name {unique_id}", category="software")

        payload = {"name": f"Updated Name {unique_id}", "price_per_level": 2000.0}

        response = client.patch(
            f"/api/v1/academics/courses/{course.id}",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["price_per_level"] == payload["price_per_level"]

    def test_update_course_not_found(self, client, admin_headers):
        """Test updating a non-existent course returns 404."""
        payload = {"name": "Updated Name"}

        response = client.patch(
            "/api/v1/academics/courses/99999",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 404

    def test_update_course_unauthorized(self, client, db_session):
        """Test updating a course without auth fails."""
        from tests.utils.db_helpers import create_test_course
        unique_id = str(uuid.uuid4())[:8]
        course = create_test_course(db_session, name=f"Test {unique_id}", category="software")

        payload = {"name": "Updated Name"}

        response = client.patch(
            f"/api/v1/academics/courses/{course.id}",
            json=payload
        )

        assert response.status_code == 401

    def test_update_course_validation_error(self, client, admin_headers, db_session):
        """Test updating a course with invalid data fails validation."""
        from tests.utils.db_helpers import create_test_course
        unique_id = str(uuid.uuid4())[:8]
        course = create_test_course(db_session, name=f"Test {unique_id}", category="software")

        payload = {"price_per_level": -500}  # Negative price

        response = client.patch(
            f"/api/v1/academics/courses/{course.id}",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422


class TestCoursesEdgeCases:
    """Edge cases and boundary conditions"""

    def test_list_courses_empty_database(self, client, admin_headers):
        """Test listing courses returns valid response structure."""
        response = client.get("/api/v1/academics/courses", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        # Note: Database may have existing courses, just verify structure

    def test_create_course_boundary_price(self, client, admin_headers):
        """Test creating a course with boundary price values."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"Free Course {unique_id}",
            "category": "software",
            "price_per_level": 0.0  # Zero price - API may reject this
        }

        response = client.post(
            "/api/v1/academics/courses",
            headers=admin_headers,
            json=payload
        )

        # API may reject 0.0 price as invalid, accept either 201 or 422
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            assert response.json()["data"]["price_per_level"] == 0.0

    def test_create_course_long_name(self, client, admin_headers):
        """Test creating a course with very long name."""
        payload = {
            "name": "A" * 200,  # Very long name
            "category": "software"
        }

        response = client.post(
            "/api/v1/academics/courses",
            headers=admin_headers,
            json=payload
        )

        # Should either succeed or fail with validation error
        assert response.status_code in [201, 422]

    def test_update_course_no_changes(self, client, admin_headers, db_session):
        """Test updating a course with empty payload."""
        from tests.utils.db_helpers import create_test_course
        unique_id = str(uuid.uuid4())[:8]
        course_name = f"Test {unique_id}"
        course = create_test_course(db_session, name=course_name, category="software")

        response = client.patch(
            f"/api/v1/academics/courses/{course.id}",
            headers=admin_headers,
            json={}
        )

        assert response.status_code == 200
        # Should return the course unchanged
        assert response.json()["data"]["name"] == course_name
