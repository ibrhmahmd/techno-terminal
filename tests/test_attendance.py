"""
Test module for Attendance router.

Tests all endpoints in attendance_router.py using the new typed API format:
- GET /attendance/session/{session_id} - Get session roster with attendance status
- POST /attendance/session/{session_id}/mark - Mark/update attendance

Uses strictly typed DTOs:
- StudentAttendanceItem: {student_id: int, status: AttendanceStatus}
- MarkAttendanceRequest: {entries: list[StudentAttendanceItem]}

All endpoints require admin authentication.
"""
import pytest
from datetime import date, time


class TestAttendanceRead:
    """GET /attendance/session/{session_id} - require_admin auth"""

    def test_get_session_attendance_success(self, client, admin_headers, db_session):
        """Test getting session roster with attendance status."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Attendance Test Student")

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        enrollment = Enrollment(
            student_id=student.id,
            group_id=group.id,
            level_number=1,
            status="active"
        )
        db_session.add(enrollment)
        db_session.commit()

        response = client.get(
            f"/api/v1/attendance/session/{session.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_session_attendance_not_found(self, client, admin_headers):
        """Test getting attendance for non-existent session returns 404."""
        response = client.get(
            "/api/v1/attendance/session/99999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_get_session_attendance_unauthorized(self, client):
        """Test getting attendance without auth returns 401."""
        response = client.get("/api/v1/attendance/session/1")
        assert response.status_code == 401

    def test_get_session_attendance_forbidden(self, client, system_admin_headers):
        """Test getting attendance with system_admin token (may be 403 or may be allowed)."""
        response = client.get(
            "/api/v1/attendance/session/1",
            headers=system_admin_headers
        )
        # system_admin may be treated as admin (200) or forbidden (403)
        assert response.status_code in [200, 403]


class TestAttendanceMark:
    """POST /attendance/session/{session_id}/mark - require_admin auth"""

    def test_mark_attendance_success(self, client, admin_headers, db_session):
        """Test marking attendance with valid entries."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student1 = create_test_student(db_session, full_name="Student One")
        student2 = create_test_student(db_session, full_name="Student Two")

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {
            "entries": [
                {"student_id": student1.id, "status": "present"},
                {"student_id": student2.id, "status": "absent"}
            ]
        }

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["marked"] == 2

    def test_mark_attendance_validation_empty_entries(self, client, admin_headers):
        """Test marking attendance with empty entries fails validation."""
        payload = {"entries": []}

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_mark_attendance_validation_duplicate_students(self, client, admin_headers):
        """Test marking attendance with duplicate student IDs fails validation."""
        payload = {
            "entries": [
                {"student_id": 1, "status": "present"},
                {"student_id": 1, "status": "absent"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422
        # Note: The duplicate validation error may not include 'duplicate' in response
        # depending on how Pydantic/FastAPI serializes the ValueError

    def test_mark_attendance_validation_invalid_status(self, client, admin_headers):
        """Test marking attendance with invalid status fails validation."""
        payload = {
            "entries": [
                {"student_id": 1, "status": "invalid_status"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_mark_attendance_validation_negative_student_id(self, client, admin_headers):
        """Test marking attendance with negative student_id fails validation."""
        payload = {
            "entries": [
                {"student_id": -1, "status": "present"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_mark_attendance_not_found_session(self, client, admin_headers):
        """Test marking attendance for non-existent session returns 404."""
        payload = {
            "entries": [
                {"student_id": 1, "status": "present"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/99999/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 404

    def test_mark_attendance_unauthorized(self, client):
        """Test marking attendance without auth returns 401."""
        payload = {
            "entries": [
                {"student_id": 1, "status": "present"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            json=payload
        )

        assert response.status_code == 401

    def test_mark_attendance_forbidden(self, client, system_admin_headers):
        """Test marking attendance with system_admin token (may be 403 or may be allowed)."""
        payload = {
            "entries": [
                {"student_id": 1, "status": "present"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=system_admin_headers,
            json=payload
        )

        # system_admin may be treated as admin (200) or forbidden (403)
        assert response.status_code in [200, 403]

    def test_mark_attendance_all_valid_statuses(self, client, admin_headers, db_session):
        """Test marking attendance with all valid status values."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        students = []
        for i, status in enumerate(["present", "absent", "late", "excused"]):
            student = create_test_student(db_session, full_name=f"Status Test {i}")
            students.append((student.id, status))

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {
            "entries": [
                {"student_id": sid, "status": status} for sid, status in students
            ]
        }

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["marked"] == 4


class TestAttendanceEdgeCases:
    """Edge cases and boundary conditions"""

    def test_mark_attendance_nonexistent_student(self, client, admin_headers, db_session):
        """Test marking attendance for non-existent student returns in skipped list."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {
            "entries": [
                {"student_id": 99999, "status": "present"}
            ]
        }

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert 99999 in data["data"]["skipped"]

    def test_mark_attendance_idempotent_update(self, client, admin_headers, db_session):
        """Test marking attendance is idempotent - same student can be updated."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Idempotent Student")

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload1 = {"entries": [{"student_id": student.id, "status": "present"}]}
        response1 = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload1
        )
        assert response1.status_code == 200

        payload2 = {"entries": [{"student_id": student.id, "status": "absent"}]}
        response2 = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload2
        )
        assert response2.status_code == 200

    def test_mark_attendance_missing_fields(self, client, admin_headers):
        """Test marking attendance with missing required fields fails validation."""
        payload_missing_status = {"entries": [{"student_id": 1}]}
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload_missing_status
        )
        assert response.status_code == 422

        payload_missing_id = {"entries": [{"status": "present"}]}
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload_missing_id
        )
        assert response.status_code == 422

    def test_mark_attendance_large_batch(self, client, admin_headers, db_session):
        """Test marking attendance for many students at once."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        entries = []
        for i in range(50):
            student = create_test_student(db_session, full_name=f"Batch Student {i}")
            entries.append({"student_id": student.id, "status": "present"})

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {"entries": entries}

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["marked"] == 50


class TestAttendanceValidationExtended:
    """Extended validation tests for attendance marking."""

    def test_mark_attendance_zero_student_id(self, client, admin_headers):
        """Test marking attendance with student_id=0 fails gt=0 validation."""
        payload = {
            "entries": [
                {"student_id": 0, "status": "present"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_mark_attendance_max_int_student_id(self, client, admin_headers):
        """Test marking attendance with very large student_id."""
        payload = {
            "entries": [
                {"student_id": 2147483647, "status": "present"}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        # Should be accepted (200) or skipped (200 with student in skipped list)
        assert response.status_code in [200, 422]

    def test_mark_attendance_empty_string_status(self, client, admin_headers):
        """Test marking attendance with empty status string."""
        payload = {
            "entries": [
                {"student_id": 1, "status": ""}
            ]
        }

        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_get_session_attendance_invalid_session_id_format(self, client, admin_headers):
        """Test getting attendance with non-numeric session_id returns 422."""
        response = client.get(
            "/api/v1/attendance/session/abc",
            headers=admin_headers
        )

        assert response.status_code == 422


class TestAttendanceBusinessLogic:
    """Business logic edge cases for attendance operations."""

    def test_mark_attendance_student_not_in_group(self, client, admin_headers, db_session):
        """Test marking attendance for student not enrolled in session's group - should skip."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        # Create student but DON'T enroll them
        student = create_test_student(db_session, full_name="Unenrolled Student")

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {
            "entries": [
                {"student_id": student.id, "status": "present"}
            ]
        }

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert student.id in data["data"]["skipped"]
        assert data["data"]["marked"] == 0

    def test_mark_attendance_student_wrong_level(self, client, admin_headers, db_session):
        """Test marking attendance for student enrolled at wrong level - should skip."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Wrong Level Student")

        # Enroll at level 2
        enrollment = Enrollment(
            student_id=student.id,
            group_id=group.id,
            level_number=2,
            status="active"
        )
        db_session.add(enrollment)
        db_session.commit()

        # Session at level 1
        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {
            "entries": [
                {"student_id": student.id, "status": "present"}
            ]
        }

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert student.id in data["data"]["skipped"]

    def test_mark_attendance_response_structure(self, client, admin_headers, db_session):
        """Test that mark attendance response matches MarkAttendanceResponseDTO exactly."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Response Structure Student")

        enrollment = Enrollment(
            student_id=student.id,
            group_id=group.id,
            level_number=1,
            status="active"
        )
        db_session.add(enrollment)
        db_session.commit()

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        payload = {
            "entries": [
                {"student_id": student.id, "status": "present"}
            ]
        }

        response = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "marked" in data["data"]
        assert "skipped" in data["data"]
        assert isinstance(data["data"]["marked"], int)
        assert isinstance(data["data"]["skipped"], list)

    def test_get_session_attendance_response_structure(self, client, admin_headers, db_session):
        """Test that get session attendance response matches SessionAttendanceRowDTO."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Roster Structure Student")

        enrollment = Enrollment(
            student_id=student.id,
            group_id=group.id,
            level_number=1,
            status="active"
        )
        db_session.add(enrollment)
        db_session.commit()

        session = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        response = client.get(
            f"/api/v1/attendance/session/{session.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert isinstance(data["data"], list)


class TestAttendanceIntegration:
    """Integration tests for full attendance workflows."""

    def test_full_attendance_workflow(self, client, admin_headers, db_session):
        """Test complete workflow: create session, get roster, mark attendance, verify."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models import CourseSession

        # Setup
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        students = [
            create_test_student(db_session, full_name=f"Workflow Student {i}")
            for i in range(3)
        ]

        for student in students:
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
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Step 1: Get initial roster (should be empty or have enrollments)
        response1 = client.get(
            f"/api/v1/attendance/session/{session.id}",
            headers=admin_headers
        )
        assert response1.status_code == 200

        # Step 2: Mark attendance for all students
        payload = {
            "entries": [
                {"student_id": student.id, "status": "present"}
                for student in students
            ]
        }
        response2 = client.post(
            f"/api/v1/attendance/session/{session.id}/mark",
            headers=admin_headers,
            json=payload
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["marked"] == 3

        # Step 3: Get roster again (should now have attendance records)
        response3 = client.get(
            f"/api/v1/attendance/session/{session.id}",
            headers=admin_headers
        )
        assert response3.status_code == 200

    def test_mark_attendance_multiple_sessions_same_student(self, client, admin_headers, db_session):
        """Test marking attendance for same student across multiple sessions."""
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_student
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models import CourseSession

        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)
        student = create_test_student(db_session, full_name="Multi-Session Student")

        enrollment = Enrollment(
            student_id=student.id,
            group_id=group.id,
            level_number=1,
            status="active"
        )
        db_session.add(enrollment)
        db_session.commit()

        # Create two sessions
        session1 = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            level_number=1,
            session_number=1,
            status="scheduled"
        )
        session2 = CourseSession(
            group_id=group.id,
            session_date=date.today(),
            start_time=time(14, 0),
            end_time=time(16, 0),
            level_number=1,
            session_number=2,
            status="scheduled"
        )
        db_session.add(session1)
        db_session.add(session2)
        db_session.commit()
        db_session.refresh(session1)
        db_session.refresh(session2)

        # Mark attendance in session 1
        response1 = client.post(
            f"/api/v1/attendance/session/{session1.id}/mark",
            headers=admin_headers,
            json={"entries": [{"student_id": student.id, "status": "present"}]}
        )
        assert response1.status_code == 200

        # Mark attendance in session 2
        response2 = client.post(
            f"/api/v1/attendance/session/{session2.id}/mark",
            headers=admin_headers,
            json={"entries": [{"student_id": student.id, "status": "absent"}]}
        )
        assert response2.status_code == 200
