"""
Test module for Sessions router.

Tests all endpoints in sessions_router.py:
- GET /academics/sessions/daily-schedule - Get daily schedule
- POST /academics/groups/{group_id}/sessions - Add extra session
- GET /academics/sessions/{session_id} - Get session details
- PATCH /academics/sessions/{session_id} - Update session
- DELETE /academics/sessions/{session_id} - Delete session
- POST /academics/sessions/{session_id}/cancel - Cancel session
- POST /academics/sessions/{session_id}/reactivate - Reactivate cancelled session
- POST /academics/sessions/{session_id}/substitute - Mark substitute instructor
"""
import pytest
from datetime import date, timedelta
from app.modules.academics.models import CourseSession


class TestSessionsRead:
    """GET endpoints - require_any auth"""

    def test_get_daily_schedule_success(self, client, admin_headers, db_session):
        """Test getting daily schedule."""
        # Create test data
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a session for today
        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()

        response = client.get(
            "/api/v1/academics/sessions/daily-schedule",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_daily_schedule_with_date(self, client, admin_headers):
        """Test getting daily schedule with specific date."""
        target_date = date.today() + timedelta(days=7)

        response = client.get(
            f"/api/v1/academics/sessions/daily-schedule?target_date={target_date.isoformat()}",
            headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_get_daily_schedule_unauthorized(self, client):
        """Test getting daily schedule without auth fails."""
        response = client.get("/api/v1/academics/sessions/daily-schedule")

        assert response.status_code == 401

    def test_get_session_details_success(self, client, admin_headers, db_session):
        """Test getting session details."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.get(
            f"/api/v1/academics/sessions/{session.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == session.id

    def test_get_session_details_not_found(self, client, admin_headers):
        """Test getting non-existent session returns 404."""
        response = client.get("/api/v1/academics/sessions/99999", headers=admin_headers)

        assert response.status_code == 404


class TestSessionsWrite:
    """POST/PATCH/DELETE - require_admin auth"""

    def test_add_extra_session_success(self, client, admin_headers, db_session):
        """Test adding an extra session to a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session_date = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "session_date": session_date,
            "level_number": 1,
            "notes": "Extra practice session"
        }

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/sessions",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["group_id"] == group.id
        assert data["data"]["session_date"] == session_date

    def test_add_extra_session_group_not_found(self, client, admin_headers):
        """Test adding session to non-existent group returns 404."""
        payload = {
            "session_date": date.today().isoformat(),
            "level_number": 1
        }

        response = client.post(
            "/api/v1/academics/groups/99999/sessions",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 404

    def test_add_extra_session_unauthorized(self, client, db_session):
        """Test adding session without auth fails."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        payload = {"session_date": date.today().isoformat(), "level_number": 1}

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/sessions",
            json=payload
        )

        assert response.status_code == 401

    def test_add_extra_session_non_admin(self, client, system_admin_headers, db_session):
        """Test adding session with non-admin token fails."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        payload = {"session_date": date.today().isoformat(), "level_number": 1}

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/sessions",
            headers=system_admin_headers,
            json=payload
        )

        assert response.status_code == 403

    def test_update_session_success(self, client, admin_headers, db_session):
        """Test updating a session."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            level_number=1,
            session_number=1,
            status="scheduled",
            notes="Original notes"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {"notes": "Updated notes"}

        response = client.patch(
            f"/api/v1/academics/sessions/{session.id}",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["notes"] == payload["notes"]

    def test_update_session_not_found(self, client, admin_headers):
        """Test updating non-existent session returns 404."""
        payload = {"notes": "Updated notes"}

        response = client.patch(
            "/api/v1/academics/sessions/99999",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 404

    def test_delete_session_success(self, client, admin_headers, db_session):
        """Test deleting a session."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.delete(
            f"/api/v1/academics/sessions/{session.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_delete_session_not_found(self, client, admin_headers):
        """Test deleting non-existent session returns 404."""
        response = client.delete("/api/v1/academics/sessions/99999", headers=admin_headers)

        assert response.status_code == 404

    def test_cancel_session_success(self, client, admin_headers, db_session):
        """Test cancelling a session."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today() + timedelta(days=1),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.post(
            f"/api/v1/academics/sessions/{session.id}/cancel",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cancelled" in data["message"].lower() or "rescheduled" in data["message"].lower()

    def test_cancel_session_not_found(self, client, admin_headers):
        """Test cancelling non-existent session returns 404."""
        response = client.post("/api/v1/academics/sessions/99999/cancel", headers=admin_headers)

        assert response.status_code == 404

    def test_reactivate_session_success(self, client, admin_headers, db_session):
        """Test reactivating a cancelled session."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a cancelled session
        session = CourseSession(
            group_id=group.id,
            session_date=date.today() + timedelta(days=1),
            level_number=1,
            status="cancelled",
            session_number=0
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.post(
            f"/api/v1/academics/sessions/{session.id}/reactivate",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reactivated" in data["message"].lower()
        assert data["data"]["status"] == "scheduled"

    def test_reactivate_session_not_found(self, client, admin_headers):
        """Test reactivating non-existent session returns 404."""
        response = client.post("/api/v1/academics/sessions/99999/reactivate", headers=admin_headers)

        assert response.status_code == 404

    def test_reactivate_non_cancelled_session(self, client, admin_headers, db_session):
        """Test reactivating a non-cancelled session returns error."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a scheduled (not cancelled) session
        session = CourseSession(
            group_id=group.id,
            session_date=date.today() + timedelta(days=1),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.post(
            f"/api/v1/academics/sessions/{session.id}/reactivate",
            headers=admin_headers
        )

        # Should return 400 for business rule violation
        assert response.status_code in [400, 409]

    def test_substitute_instructor_success(self, client, admin_headers, db_session):
        """Test marking substitute instructor."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        from app.modules.hr.models import Employee

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create an employee as substitute instructor
        employee = Employee(full_name="Substitute Instructor", is_active=True)
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {"instructor_id": employee.id}

        response = client.post(
            f"/api/v1/academics/sessions/{session.id}/substitute",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSessionsEdgeCases:
    """Edge cases and boundary conditions"""

    def test_add_session_past_date(self, client, admin_headers, db_session):
        """Test adding session in the past."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        past_date = (date.today() - timedelta(days=30)).isoformat()
        payload = {
            "session_date": past_date,
            "level_number": 1
        }

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/sessions",
            headers=admin_headers,
            json=payload
        )

        # May succeed or fail depending on business rules
        assert response.status_code in [201, 400, 422]

    def test_add_session_duplicate_date(self, client, admin_headers, db_session):
        """Test adding session on same date as existing session."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session_date = (date.today() + timedelta(days=1)).isoformat()

        # Create first session
        session1 = CourseSession(
            group_id=group.id,
            session_date=session_date,
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session1)
        db_session.commit()

        # Try to create second on same date
        payload = {
            "session_date": session_date,
            "level_number": 1
        }

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/sessions",
            headers=admin_headers,
            json=payload
        )

        # May succeed or fail depending on business rules
        assert response.status_code in [201, 400, 409]

    def test_cancel_already_cancelled_session(self, client, admin_headers, db_session):
        """Test cancelling an already cancelled session."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today() + timedelta(days=1),
            level_number=1,
            session_number=1,
            status="cancelled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.post(
            f"/api/v1/academics/sessions/{session.id}/cancel",
            headers=admin_headers
        )

        # May return 200 (idempotent) or 400 if already cancelled
        assert response.status_code in [200, 400]

    def test_cancel_and_reactivate_workflow(self, client, admin_headers, db_session):
        """Test full cancel and reactivate workflow with session numbering."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        from datetime import time
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = CourseSession(
                group_id=group.id,
                session_date=date.today() + timedelta(days=i+1),
                level_number=1,
                session_number=i+1,
                start_time=time(10, 0),
                end_time=time(12, 0),
                status="scheduled"
            )
            db_session.add(session)
            sessions.append(session)
        db_session.commit()
        for s in sessions:
            db_session.refresh(s)

        # Cancel session 2
        cancel_response = client.post(
            f"/api/v1/academics/sessions/{sessions[1].id}/cancel",
            headers=admin_headers
        )
        assert cancel_response.status_code == 200

        # Verify session 2 is cancelled
        get_response = client.get(
            f"/api/v1/academics/sessions/{sessions[1].id}",
            headers=admin_headers
        )
        assert get_response.json()["data"]["status"] == "cancelled"

        # Reactivate session 2
        reactivate_response = client.post(
            f"/api/v1/academics/sessions/{sessions[1].id}/reactivate",
            headers=admin_headers
        )
        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["data"]["status"] == "scheduled"

    def test_cancel_session_updates_attendance(self, client, admin_headers, db_session):
        """Test that cancelling a session marks attendances as cancelled."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.attendance.models.attendance_models import Attendance
        from datetime import time

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Attendance Test Student")

        # Create enrollment
        enrollment = Enrollment(
            student_id=student.id,
            group_id=group.id,
            level_number=1,
            status="active"
        )
        db_session.add(enrollment)
        db_session.commit()

        # Create session
        session = CourseSession(
            group_id=group.id,
            session_date=date.today() + timedelta(days=1),
            level_number=1,
            session_number=1,
            start_time=time(10, 0),
            end_time=time(12, 0),
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Create attendance record
        attendance = Attendance(
            student_id=student.id,
            session_id=session.id,
            enrollment_id=enrollment.id,
            status="present",
            marked_at=date.today()
        )
        db_session.add(attendance)
        db_session.commit()

        # Cancel the session
        response = client.post(
            f"/api/v1/academics/sessions/{session.id}/cancel",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify attendance is now cancelled
        db_session.refresh(attendance)
        assert attendance.status == "cancelled"
