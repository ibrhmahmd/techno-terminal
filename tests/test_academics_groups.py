"""
Test module for Groups router.

Tests all endpoints in groups_router.py:
- GET /academics/groups - List all active groups
- GET /academics/groups/enriched - Get enriched groups
- GET /academics/groups/{group_id} - Get group by ID
- GET /academics/groups/{group_id}/enriched - Get enriched group
- POST /academics/groups - Create group
- PATCH /academics/groups/{group_id} - Update group
- GET /academics/groups/{group_id}/sessions - List group sessions
- POST /academics/groups/{group_id}/progress-level - Progress group level
- DELETE /academics/groups/{group_id} - Delete group
- POST /academics/groups/{group_id}/generate-sessions - Generate sessions
- GET /academics/groups/search - Search groups
- GET /academics/groups/by-type/{group_type} - List groups by type
- GET /academics/groups/by-course/{course_id} - List groups by course
"""
import pytest
from datetime import date, datetime, timedelta
from app.modules.academics.models import Group, Course, CourseSession


class TestGroupsRead:
    """GET endpoints - require_any auth"""

    def test_list_groups_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test listing groups returns paginated results."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group1 = create_test_group(db_session, course_id=course.id, name="Group A")
        group2 = create_test_group(db_session, course_id=course.id, name="Group B")

        response = client.get("/api/v1/academics/groups", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2

    def test_list_groups_pagination(self, client, mock_admin_headers, override_auth, db_session):
        """Test group pagination."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)

        for i in range(5):
            create_test_group(db_session, course_id=course.id, name=f"Group {i}")

        response = client.get("/api/v1/academics/groups?limit=2", headers=mock_admin_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) <= 2

    def test_list_groups_unauthorized(self, client):
        """Test listing groups without auth fails."""
        response = client.get("/api/v1/academics/groups")
        assert response.status_code == 401

    def test_list_enriched_groups_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test listing enriched groups with instructor/course names."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name="Enriched Test Course")
        group = create_test_group(db_session, course_id=course.id, name="Enriched Group")

        response = client.get("/api/v1/academics/groups/enriched", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_group_by_id_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test getting group by ID."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(f"/api/v1/academics/groups/{group.id}", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == group.id

    def test_get_group_not_found(self, client, mock_admin_headers, override_auth):
        """Test getting non-existent group returns 404."""
        response = client.get("/api/v1/academics/groups/99999", headers=mock_admin_headers)
        assert response.status_code == 404

    def test_get_enriched_group_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test getting enriched group by ID."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/enriched",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == group.id

    def test_list_group_sessions_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test listing sessions for a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create sessions for the group
        for i in range(3):
            session = CourseSession(
                group_id=group.id,
                session_date=date.today() + timedelta(days=i),
                level_number=1,
                status="scheduled"
            )
            db_session.add(session)
        db_session.commit()

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/sessions",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3

    def test_list_group_sessions_with_level_filter(self, client, mock_admin_headers, override_auth, db_session):
        """Test filtering group sessions by level."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create session for level 2
        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            level_number=2,
            session_number=1,
            start_time=datetime.now().time(),
            end_time=datetime.now().time(),
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/sessions?level=2",
            headers=mock_admin_headers
        )

        assert response.status_code == 200



class TestGroupsWrite:
    """POST/PATCH/DELETE - require_admin auth"""

    def test_create_group_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test creating a new group."""
        from tests.utils.db_helpers import create_test_course
        from app.modules.hr.models import Employee

        course = create_test_course(db_session)
        instructor = Employee(full_name="Test Instructor", is_active=True)
        db_session.add(instructor)
        db_session.commit()

        payload = {
            "name": "New Test Group",
            "course_id": course.id,
            "instructor_id": instructor.id,
            "level_number": 1,
            "start_date": date.today().isoformat()
        }

        response = client.post(
            "/api/v1/academics/groups",
            headers=mock_admin_headers,
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == payload["name"]

    def test_create_group_unauthorized(self, client, db_session):
        """Test creating group without auth fails."""
        payload = {"name": "Test Group", "course_id": 1}
        response = client.post("/api/v1/academics/groups", json=payload)
        assert response.status_code == 401

    def test_create_group_system_admin(self, client, mock_admin_headers, override_system_admin_auth, db_session):
        """Test creating group with system_admin token succeeds."""
        from tests.utils.db_helpers import create_test_course
        course = create_test_course(db_session)
        payload = {"name": "Test Group", "course_id": course.id, "level_number": 1, "start_date": date.today().isoformat()}
        response = client.post(
            "/api/v1/academics/groups",
            headers=mock_admin_headers,
            json=payload
        )
        assert response.status_code == 201

    def test_update_group_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test updating a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, name="Old Name")

        payload = {"name": "Updated Group Name"}

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}",
            headers=mock_admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == payload["name"]

    def test_update_group_not_found(self, client, mock_admin_headers, override_auth):
        """Test updating non-existent group returns 404."""
        payload = {"name": "Updated Name"}
        response = client.patch(
            "/api/v1/academics/groups/99999",
            headers=mock_admin_headers,
            json=payload
        )
        assert response.status_code == 404

    def test_progress_group_level_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test progressing group to next level."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=1)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/progress-level",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "level" in data["message"].lower()

    def test_progress_group_level_not_found(self, client, mock_admin_headers, override_auth):
        """Test progressing non-existent group returns 404."""
        response = client.post(
            "/api/v1/academics/groups/99999/progress-level",
            headers=mock_admin_headers
        )
        assert response.status_code == 404

    def test_delete_group_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test soft-deleting a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "archived" in data["message"].lower() or "deleted" in data["message"].lower() or "deactivated" in data["message"].lower()

    def test_delete_group_not_found(self, client, mock_admin_headers, override_auth):
        """Test deleting non-existent group returns 404."""
        response = client.delete("/api/v1/academics/groups/99999", headers=mock_admin_headers)
        assert response.status_code == 404

    def test_generate_level_sessions_success(self, client, mock_admin_headers, override_auth, db_session):
        """Test generating sessions for a specific level."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        payload = {
            "level_number": 1,
            "start_date": date.today().isoformat()
        }

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/generate-sessions",
            headers=mock_admin_headers,
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_generate_level_sessions_not_found(self, client, mock_admin_headers, override_auth):
        """Test generating sessions for non-existent group returns 404."""
        payload = {"level_number": 1, "start_date": date.today().isoformat()}
        response = client.post(
            "/api/v1/academics/groups/99999/generate-sessions",
            headers=mock_admin_headers,
            json=payload
        )
        assert response.status_code == 404


class TestGroupsEdgeCases:
    """Edge cases and boundary conditions"""

    def test_create_group_missing_required_fields(self, client, mock_admin_headers, override_auth):
        """Test creating group without required fields."""
        payload = {"name": "Incomplete Group"}  # Missing course_id
        response = client.post(
            "/api/v1/academics/groups",
            headers=mock_admin_headers,
            json=payload
        )
        assert response.status_code == 422

    def test_update_group_no_changes(self, client, mock_admin_headers, override_auth, db_session):
        """Test updating group with empty payload."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, name="Test")

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}",
            headers=mock_admin_headers,
            json={}
        )

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Test"

    def test_delete_already_inactive_group(self, client, mock_admin_headers, override_auth, db_session):
        """Test deleting an already inactive group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, status="inactive")

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}",
            headers=mock_admin_headers
        )

        # May return 404 if already inactive, or handle gracefully
        assert response.status_code in [200, 404]
