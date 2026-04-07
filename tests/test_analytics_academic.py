"""
Test module for Academic Analytics router.

Tests all endpoints in app/api/routers/analytics/academic.py:
- GET /analytics/dashboard/summary
- GET /analytics/academics/unpaid-attendees
- GET /analytics/academics/groups/{group_id}/roster
- GET /analytics/academics/groups/{group_id}/heatmap
- GET /analytics/academics/student-progress
- GET /analytics/academics/course-completion

All endpoints require admin authentication.
"""
from datetime import date, timedelta


class TestDashboardSummary:
    """GET /analytics/dashboard/summary - require_admin auth"""

    def test_dashboard_summary_success(self, client, admin_headers):
        """Test getting dashboard summary with active enrollments and session count."""
        response = client.get(
            "/api/v1/analytics/dashboard/summary",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

        dashboard_data = data["data"]
        assert "active_enrollments" in dashboard_data
        assert "today_sessions_count" in dashboard_data
        assert isinstance(dashboard_data["active_enrollments"], int)
        assert isinstance(dashboard_data["today_sessions_count"], int)
        assert dashboard_data["active_enrollments"] >= 0
        assert dashboard_data["today_sessions_count"] >= 0

    def test_dashboard_summary_unauthorized(self, client):
        """Test getting dashboard summary without auth returns 401."""
        response = client.get("/api/v1/analytics/dashboard/summary")
        assert response.status_code == 401

    def test_dashboard_summary_forbidden(self, client, system_admin_headers):
        """Test getting dashboard summary with system_admin token (may be 200 or 403)."""
        response = client.get(
            "/api/v1/analytics/dashboard/summary",
            headers=system_admin_headers
        )
        assert response.status_code in [200, 403]


class TestUnpaidAttendees:
    """GET /analytics/academics/unpaid-attendees - require_admin auth"""

    def test_unpaid_attendees_success(self, client, admin_headers):
        """Test getting unpaid attendees without date filter."""
        response = client.get(
            "/api/v1/analytics/academics/unpaid-attendees",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_unpaid_attendees_with_target_date(self, client, admin_headers):
        """Test getting unpaid attendees with specific target date."""
        today = date.today().isoformat()
        response = client.get(
            f"/api/v1/analytics/academics/unpaid-attendees?target_date={today}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_unpaid_attendees_unauthorized(self, client):
        """Test getting unpaid attendees without auth returns 401."""
        response = client.get("/api/v1/analytics/academics/unpaid-attendees")
        assert response.status_code == 401

    def test_unpaid_attendees_forbidden(self, client, system_admin_headers):
        """Test getting unpaid attendees with system_admin token (may be 200 or 403)."""
        response = client.get(
            "/api/v1/analytics/academics/unpaid-attendees",
            headers=system_admin_headers
        )
        assert response.status_code in [200, 403]


class TestGroupRoster:
    """GET /analytics/academics/groups/{group_id}/roster - require_admin auth"""

    def test_group_roster_success(self, client, admin_headers, db_session):
        """Test getting group roster with valid group and level."""
        from tests.utils.db_helpers import create_test_course, create_test_group

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/analytics/academics/groups/{group.id}/roster?level_number=1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_group_roster_missing_level(self, client, admin_headers):
        """Test getting group roster without required level_number returns 422."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/roster",
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_group_roster_not_found(self, client, admin_headers):
        """Test getting roster for non-existent group returns 404 or empty list."""
        response = client.get(
            "/api/v1/analytics/academics/groups/99999/roster?level_number=1",
            headers=admin_headers
        )
        # May return 200 with empty list or 404 depending on implementation
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["data"], list)

    def test_group_roster_invalid_level(self, client, admin_headers):
        """Test getting roster with invalid level_number returns 422."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/roster?level_number=0",
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_group_roster_unauthorized(self, client):
        """Test getting group roster without auth returns 401."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/roster?level_number=1"
        )
        assert response.status_code == 401


class TestAttendanceHeatmap:
    """GET /analytics/academics/groups/{group_id}/heatmap - require_admin auth"""

    def test_attendance_heatmap_success(self, client, admin_headers, db_session):
        """Test getting attendance heatmap with valid group and level."""
        from tests.utils.db_helpers import create_test_course, create_test_group

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/analytics/academics/groups/{group.id}/heatmap?level_number=1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_attendance_heatmap_missing_level(self, client, admin_headers):
        """Test getting heatmap without required level_number returns 422."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/heatmap",
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_attendance_heatmap_not_found(self, client, admin_headers):
        """Test getting heatmap for non-existent group returns 404 or empty list."""
        response = client.get(
            "/api/v1/analytics/academics/groups/99999/heatmap?level_number=1",
            headers=admin_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["data"], list)

    def test_attendance_heatmap_invalid_level(self, client, admin_headers):
        """Test getting heatmap with invalid level_number returns 422."""
        response = client.get(
            "/api/v1/analytics/academics/groups/1/heatmap?level_number=0",
            headers=admin_headers
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

    def test_student_progress_all(self, client, admin_headers):
        """Test getting student progress without filters."""
        response = client.get(
            "/api/v1/analytics/academics/student-progress",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_student_progress_by_student_id(self, client, admin_headers, db_session):
        """Test getting student progress filtered by student_id."""
        from tests.utils.db_helpers import create_test_student

        student = create_test_student(db_session, full_name="Progress Test Student")

        response = client.get(
            f"/api/v1/analytics/academics/student-progress?student_id={student.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_student_progress_by_group_id(self, client, admin_headers, db_session):
        """Test getting student progress filtered by group_id."""
        from tests.utils.db_helpers import create_test_course, create_test_group

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/analytics/academics/student-progress?group_id={group.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_student_progress_by_both_filters(self, client, admin_headers, db_session):
        """Test getting student progress with both student_id and group_id filters."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Filtered Student")

        response = client.get(
            f"/api/v1/analytics/academics/student-progress?student_id={student.id}&group_id={group.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_student_progress_not_found_student(self, client, admin_headers):
        """Test getting progress for non-existent student returns empty list."""
        response = client.get(
            "/api/v1/analytics/academics/student-progress?student_id=99999",
            headers=admin_headers
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

    def test_course_completion_success(self, client, admin_headers):
        """Test getting course completion rates."""
        response = client.get(
            "/api/v1/analytics/academics/course-completion",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_course_completion_empty(self, client, admin_headers):
        """Test course completion when no completion data exists."""
        response = client.get(
            "/api/v1/analytics/academics/course-completion",
            headers=admin_headers
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

    def test_course_completion_forbidden(self, client, system_admin_headers):
        """Test getting course completion with system_admin token (may be 200 or 403)."""
        response = client.get(
            "/api/v1/analytics/academics/course-completion",
            headers=system_admin_headers
        )
        assert response.status_code in [200, 403]
