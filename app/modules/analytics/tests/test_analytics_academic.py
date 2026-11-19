"""
Test module for Academic Analytics router.

Tests all endpoints in app/api/routers/analytics/academic.py:
- GET /analytics/dashboard/summary
- GET /analytics/academics/unpaid-attendees
- GET /analytics/academics/groups/{group_id}/heatmap
- GET /analytics/academics/student-progress
- GET /analytics/academics/course-completion

All endpoints require admin authentication.
"""
from datetime import date, timedelta
from app.shared.datetime_utils import cairo_today

import pytest


class TestUnpaidAttendees:
    """GET /analytics/academics/unpaid-attendees - require_admin auth"""

    def test_unpaid_attendees_success(self, client, mock_admin_headers, override_auth):
        """Test getting unpaid attendees without date filter."""
        response = client.get(
            "/api/v1/analytics/academics/unpaid-attendees",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_unpaid_attendees_with_target_date(self, client, mock_admin_headers, override_auth):
        """Test getting unpaid attendees with specific target date."""
        today = cairo_today().isoformat()
        response = client.get(
            f"/api/v1/analytics/academics/unpaid-attendees?target_date={today}",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_unpaid_attendees_unauthorized(self, client):
        """Test getting unpaid attendees without auth returns 401."""
        response = client.get("/api/v1/analytics/academics/unpaid-attendees")
        assert response.status_code == 401

    def test_unpaid_attendees_system_admin_allowed(
        self, client, system_admin_headers, override_system_admin_auth
    ):
        """A system_admin user may read unpaid attendees (200)."""
        response = client.get(
            "/api/v1/analytics/academics/unpaid-attendees",
            headers=system_admin_headers
        )
        assert response.status_code == 200


class TestAttendanceHeatmap:
    """GET /analytics/academics/groups/{group_id}/heatmap - require_admin auth"""

    def test_attendance_heatmap_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test getting attendance heatmap with valid group and level."""
        from app.testing.db_helpers import create_test_course, create_test_group

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/analytics/academics/groups/{group.id}/heatmap?level_number=1",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_attendance_heatmap_missing_level(self, client, mock_admin_headers, override_auth):
        """Test getting heatmap without required level_number returns 422."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/heatmap",
            headers=mock_admin_headers
        )
        assert response.status_code == 422

    def test_attendance_heatmap_not_found(self, client, mock_admin_headers, override_auth):
        """Heatmap for a non-existent group is 404 NotFoundError (#143)."""
        response = client.get(
            "/api/v1/analytics/academics/groups/99999999/heatmap?level_number=1",
            headers=mock_admin_headers
        )
        assert response.status_code == 404
        assert response.json()["error"] == "NotFoundError"

    def test_attendance_heatmap_invalid_level(self, client, mock_admin_headers, override_auth):
        """Test getting heatmap with invalid level_number returns 422."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/heatmap?level_number=0",
            headers=mock_admin_headers
        )
        assert response.status_code == 422

    def test_attendance_heatmap_unauthorized(self, client):
        """Test getting heatmap without auth returns 401."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/heatmap?level_number=1"
        )
        assert response.status_code == 401


class TestStudentProgress:
    """GET /analytics/academics/student-progress - require_admin auth"""

    def test_student_progress_all(self, client, mock_admin_headers, override_auth):
        """Test getting student progress without filters."""
        response = client.get(
            "/api/v1/analytics/academics/student-progress",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_student_progress_by_student_id(self, client, mock_admin_headers, override_auth, db_session):
        """Test getting student progress filtered by student_id."""
        from app.testing.db_helpers import create_test_student

        student = create_test_student(db_session, full_name="Progress Test Student")

        response = client.get(
            f"/api/v1/analytics/academics/student-progress?student_id={student.id}",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_student_progress_by_group_id(self, client, mock_admin_headers, override_auth, db_session):
        """Test getting student progress filtered by group_id."""
        from app.testing.db_helpers import create_test_course, create_test_group

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/analytics/academics/student-progress?group_id={group.id}",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_student_progress_by_both_filters(self, client, mock_admin_headers, override_auth, db_session):
        """Test getting student progress with both student_id and group_id filters."""
        from app.testing.db_helpers import create_test_course, create_test_group, create_test_student

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Filtered Student")

        response = client.get(
            f"/api/v1/analytics/academics/student-progress?student_id={student.id}&group_id={group.id}",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_student_progress_not_found_student(self, client, mock_admin_headers, override_auth):
        """Test getting progress for non-existent student returns empty list."""
        response = client.get(
            "/api/v1/analytics/academics/student-progress?student_id=99999",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0

    def test_student_progress_unauthorized(self, client):
        """Test getting student progress without auth returns 401."""
        response = client.get("/api/v1/analytics/academics/student-progress")
        assert response.status_code == 401


class TestCourseCompletion:
    """GET /analytics/academics/course-completion - require_admin auth"""

    def test_course_completion_success(self, client, mock_admin_headers, override_auth):
        """Test getting course completion rates."""
        response = client.get(
            "/api/v1/analytics/academics/course-completion",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_course_completion_empty(self, client, mock_admin_headers, override_auth):
        """Test course completion when no completion data exists."""
        response = client.get(
            "/api/v1/analytics/academics/course-completion",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should return list even if empty
        assert isinstance(data["data"], list)

    def test_course_completion_unauthorized(self, client):
        """Test getting course completion without auth returns 401."""
        response = client.get("/api/v1/analytics/academics/course-completion")
        assert response.status_code == 401

    def test_course_completion_system_admin_allowed(
        self, client, system_admin_headers, override_system_admin_auth
    ):
        """A system_admin user may read course completion (200)."""
        response = client.get(
            "/api/v1/analytics/academics/course-completion",
            headers=system_admin_headers
        )
        assert response.status_code == 200
