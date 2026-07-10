import pytest
from app.modules.academics.models import GroupLevel, Group, Course
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.academics.models.group_level_models import EnrollmentLevelHistory
from app.modules.academics.models.session_models import CourseSession
from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee
from datetime import date


class TestGroupLevelsFeature:
    """Tests for Group Level Delete (Undo) and Edit endpoints."""

    def test_delete_latest_level_clean_success(self, client, mock_admin_headers, override_auth, db_session):
        """T008, T009, T011: Delete the latest level when no payments or attendance exist."""
        course = create_test_course(db_session)
        instructor = create_test_employee(db_session)
        group = create_test_group(db_session, course_id=course.id, instructor_id=instructor.id, level_number=2)

        # Create level 1 (completed)
        level1 = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, instructor_id=instructor.id, status="completed")
        # Create level 2 (active - latest)
        level2 = GroupLevel(group_id=group.id, level_number=2, course_id=course.id, instructor_id=instructor.id, status="active")
        db_session.add(level1)
        db_session.add(level2)
        db_session.commit()

        level2_id = level2.id
        level1_id = level1.id

        # Delete level 2
        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/levels/2",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["level_number_deleted"] == 2
        assert data["data"]["reverted_to_level"] == 1
        assert data["data"]["group_level_number_after"] == 1

        # Assert level 2 is gone from DB
        db_session.expire_all()
        assert db_session.get(GroupLevel, level2_id) is None
        # Assert group level_number rolled back
        assert db_session.get(Group, group.id).level_number == 1
        # Assert level 1 status was reverted to active
        assert db_session.get(GroupLevel, level1_id).status == "active"

    def test_delete_level_not_latest_blocked(self, client, mock_admin_headers, override_auth, db_session):
        """Test deleting a level that is not the latest is blocked."""
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=2)

        level1 = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, status="completed")
        level2 = GroupLevel(group_id=group.id, level_number=2, course_id=course.id, status="active")
        db_session.add(level1)
        db_session.add(level2)
        db_session.commit()

        # Try to delete level 1 (latest is 2)
        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/levels/1",
            headers=mock_admin_headers
        )
        assert response.status_code == 409
        assert "can only delete the latest level" in response.json()["message"].lower()

    def test_delete_level_one_blocked(self, client, mock_admin_headers, override_auth, db_session):
        """Test deleting Level 1 is blocked if it's the only level."""
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=1)
        level1 = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, status="active")
        db_session.add(level1)
        db_session.commit()

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/levels/1",
            headers=mock_admin_headers
        )
        assert response.status_code == 409
        assert "cannot delete the first/only level" in response.json()["message"].lower()

    def test_delete_level_blocked_by_attendance(self, client, mock_admin_headers, override_auth, db_session):
        """Test deleting is blocked when attendance records exist."""
        from app.modules.attendance.models.attendance_models import Attendance
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=2)
        level1 = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, status="completed")
        level2 = GroupLevel(group_id=group.id, level_number=2, course_id=course.id, status="active")
        db_session.add(level1)
        db_session.add(level2)
        db_session.commit()

        # Create session and attendance
        session = CourseSession(group_id=group.id, group_level_id=level2.id, level_number=2, session_number=1, session_date=date.today())
        db_session.add(session)
        db_session.commit()

        attendance = Attendance(student_id=1, session_id=session.id, enrollment_id=1, status="present")
        db_session.add(attendance)
        db_session.commit()

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/levels/2",
            headers=mock_admin_headers
        )
        assert response.status_code == 409
        assert "attendance records" in response.json()["message"].lower()

    def test_delete_level_blocked_by_payments(self, client, mock_admin_headers, override_auth, db_session):
        """Test deleting is blocked when payment records exist."""
        from app.modules.finance.models.payment import Payment
        from app.modules.finance.models.receipt import Receipt
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=2)
        level1 = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, status="completed")
        level2 = GroupLevel(group_id=group.id, level_number=2, course_id=course.id, status="active")
        db_session.add(level1)
        db_session.add(level2)
        db_session.commit()

        # Create enrollment and payment
        enrollment = Enrollment(student_id=1, group_id=group.id, level_number=2, amount_due=100.0, status="active")
        db_session.add(enrollment)
        db_session.commit()

        receipt = Receipt(payer_name="Test Payer", payment_method="cash")
        db_session.add(receipt)
        db_session.commit()

        payment = Payment(receipt_id=receipt.id, student_id=1, enrollment_id=enrollment.id, amount=100.0, transaction_type="payment")
        db_session.add(payment)
        db_session.commit()

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/levels/2",
            headers=mock_admin_headers
        )
        assert response.status_code == 409
        assert "payments" in response.json()["message"].lower()

    def test_edit_level_success(self, client, mock_admin_headers, override_auth, db_session):
        """T012, T013, T014: Edit level details successfully."""
        course1 = create_test_course(db_session)
        course2 = create_test_course(db_session)
        instructor1 = create_test_employee(db_session)
        instructor2 = create_test_employee(db_session)
        group = create_test_group(db_session, course_id=course1.id, instructor_id=instructor1.id, level_number=1)

        level = GroupLevel(group_id=group.id, level_number=1, course_id=course1.id, instructor_id=instructor1.id, status="active")
        db_session.add(level)
        db_session.commit()

        payload = {
            "instructor_id": instructor2.id,
            "course_id": course2.id,
            "price_override": 500.00,
            "notes": "Updated mid-round notes"
        }

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}/levels/1",
            json=payload,
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["instructor_id"] == instructor2.id
        assert data["data"]["course_id"] == course2.id
        assert float(data["data"]["price_override"]) == 500.00
        assert data["data"]["notes"] == "Updated mid-round notes"

        # Assert DB values updated
        db_session.expire_all()
        db_level = db_session.get(GroupLevel, level.id)
        assert db_level.instructor_id == instructor2.id
        assert db_level.course_id == course2.id
        assert float(db_level.price_override) == 500.00
        assert db_level.notes == "Updated mid-round notes"

        # Assert parent group is UNCHANGED (per spec decision 3)
        db_group = db_session.get(Group, group.id)
        assert db_group.course_id == course1.id

    def test_edit_completed_level_blocked(self, client, mock_admin_headers, override_auth, db_session):
        """Test that editing completed levels is blocked."""
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=1)
        level = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, status="completed")
        db_session.add(level)
        db_session.commit()

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}/levels/1",
            json={"notes": "Should block"},
            headers=mock_admin_headers
        )
        assert response.status_code == 400
        assert "cannot edit" in response.json()["message"].lower()

    def test_cancel_level_with_reason_and_rollback(self, client, mock_admin_headers, override_auth, db_session):
        """T015, T016, T017: Cancel level with reason and rollback group level_number."""
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id, level_number=2)
        level1 = GroupLevel(group_id=group.id, level_number=1, course_id=course.id, status="completed")
        level2 = GroupLevel(group_id=group.id, level_number=2, course_id=course.id, status="active")
        db_session.add(level1)
        db_session.add(level2)
        db_session.commit()

        level2_id = level2.id

        payload = {"reason": "Not enough registrations"}
        response = client.post(
            f"/api/v1/academics/groups/{group.id}/levels/2/cancel",
            json=payload,
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "cancelled"

        # Assert level cancelled in DB
        db_session.expire_all()
        db_level = db_session.get(GroupLevel, level2_id)
        assert db_level.status == "cancelled"
        assert "cancelled" in db_level.notes.lower()

        # Assert group.level_number rolled back to 1
        db_group = db_session.get(Group, group.id)
        assert db_group.level_number == 1
