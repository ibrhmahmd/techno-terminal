"""
Test module for Group Lifecycle router.

Tests active endpoints in group_lifecycle_router.py:
- GET /academics/groups/{group_id}/levels/{level_number} - Get level details
- POST /academics/groups/{group_id}/levels/{level_number}/complete - Complete level
- POST /academics/groups/{group_id}/levels/{level_number}/cancel - Cancel level
- GET /academics/groups/{group_id}/enrollments/analytics - Enrollment analytics
- GET /academics/groups/{group_id}/instructors/analytics - Instructor analytics
- GET /academics/groups/{group_id}/enrollment-history - Enrollment history alias
- GET /academics/groups/{group_id}/instructor-history - Instructor history alias

DEPRECATED (removed):
- GET /academics/groups/{group_id}/history (replaced by /levels/detailed)
- GET /academics/groups/{group_id}/levels (replaced by /levels/detailed)
- GET /academics/groups/{group_id}/courses/history (replaced by lookup table)
- GET /academics/groups/{group_id}/enrollments/history (replaced by /enrollments/all)
- GET /academics/groups/{group_id}/levels/analytics (merged into /levels/detailed)
"""
from app.modules.academics.models import GroupLevel


class TestGroupLifecycleRead:
    """GET endpoints - require_any auth"""

    def test_get_group_level_details_success(self, client, admin_headers, db_session):
        """Test getting specific level details."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        level = GroupLevel(
            group_id=group.id,
            level_number=1,
            course_id=course.id,
            status="active"
        )
        db_session.add(level)
        db_session.commit()

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/levels/1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["level_number"] == 1

    def test_get_group_level_not_found(self, client, admin_headers, db_session):
        """Test getting non-existent level returns 404."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/levels/999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_get_group_enrollment_analytics_success(self, client, admin_headers, db_session):
        """Test getting enrollment analytics."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/enrollments/analytics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_group_instructor_analytics_success(self, client, admin_headers, db_session):
        """Test getting instructor assignment analytics."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/instructors/analytics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_enrollment_history_alias(self, client, admin_headers, db_session):
        """Test enrollment history alias endpoint."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/enrollment-history",
            headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_get_instructor_history_alias(self, client, admin_headers, db_session):
        """Test instructor history alias endpoint."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/instructor-history",
            headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_analytics_pagination(self, client, admin_headers, db_session):
        """Test analytics pagination parameters."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/enrollments/analytics?skip=0&limit=10",
            headers=admin_headers
        )

        assert response.status_code == 200


class TestGroupLifecycleWrite:
    """POST endpoints - require_admin auth"""

    def test_complete_group_level_success(self, client, admin_headers, db_session):
        """Test completing a group level."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=1)

        # Create active level
        level = GroupLevel(
            group_id=group.id,
            level_number=1,
            course_id=course.id,
            status="active"
        )
        db_session.add(level)
        db_session.commit()

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/1/complete",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "progressed" in data["message"].lower()

    def test_complete_group_level_not_found(self, client, admin_headers, db_session):
        """Test completing non-existent level returns 404/400."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/999/complete",
            headers=admin_headers
        )

        assert response.status_code in [400, 404]

    def test_complete_group_level_unauthorized(self, client, db_session):
        """Test completing level without auth fails."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(f"/api/v1/academics/groups/{group.id}/levels/1/complete")
        assert response.status_code == 401

    def test_cancel_group_level_success(self, client, admin_headers, db_session):
        """Test cancelling a group level."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=1)

        # Create active level
        level = GroupLevel(
            group_id=group.id,
            level_number=1,
            course_id=course.id,
            status="active"
        )
        db_session.add(level)
        db_session.commit()

        payload = {"reason": "Not enough students enrolled"}

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cancelled" in data["message"].lower()

    def test_cancel_group_level_not_found(self, client, admin_headers, db_session):
        """Test cancelling non-existent level returns 404/400."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        payload = {"reason": "Test cancellation"}

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/999/cancel",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code in [400, 404]

    def test_cancel_already_completed_level(self, client, admin_headers, db_session):
        """Test cancelling an already completed level fails."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create completed level
        level = GroupLevel(
            group_id=group.id,
            level_number=1,
            course_id=course.id,
            status="completed"
        )
        db_session.add(level)
        db_session.commit()

        payload = {"reason": "Should fail"}

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
            headers=admin_headers,
            json=payload
        )

        # Should fail because level is already completed
        assert response.status_code == 400


class TestGroupLifecycleEdgeCases:
    """Edge cases and boundary conditions"""

    def test_complete_group_no_active_level(self, client, admin_headers, db_session):
        """Test completing when no active level exists."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/1/complete",
            headers=admin_headers
        )

        assert response.status_code in [400, 404]

    def test_analytics_invalid_pagination(self, client, admin_headers, db_session):
        """Test analytics with invalid pagination params."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/enrollments/analytics?skip=-1&limit=0",
            headers=admin_headers
        )

        # Should return 422 for invalid params
        assert response.status_code in [200, 422]
