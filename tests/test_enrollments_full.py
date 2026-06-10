"""
tests/test_enrollments_full.py
───────────────────────────────
Comprehensive tests for all 7 enrollment endpoints.

Endpoints:
  POST   /api/v1/enrollments                    → Enroll student (201)
  PATCH  /api/v1/enrollments/{enrollment_id}     → Update enrollment (200)
  DELETE /api/v1/enrollments/{enrollment_id}     → Drop enrollment (200)
  POST   /api/v1/enrollments/transfer            → Transfer student (200)
  GET    /api/v1/enrollments/student/{student_id} → Student enrollment history (200)
  POST   /api/v1/enrollments/{enrollment_id}/discount → Apply sibling discount (200)
  GET    /api/v1/enrollments/group/{group_id}/students-summary → Group summary (200)
"""
import pytest
from uuid import uuid4


class TestEnrollmentCreate:
    """POST /api/v1/enrollments — Enroll a student in a group."""

    def test_enroll_student_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={
                "student_id": student.id,
                "group_id": group.id,
                "amount_due": 500.0,
                "discount": 50.0,
                "notes": "Test enrollment",
            },
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["student_id"] == student.id
        assert data["data"]["group_id"] == group.id
        assert data["data"]["amount_due"] == 500.0
        assert data["data"]["status"] == "active"
        assert "enrolled_at" in data["data"]

    def test_enroll_student_with_amount_due(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={
                "student_id": student.id,
                "group_id": group.id,
                "amount_due": 300.0,
                "discount": 0.0,
                "notes": "Custom amount",
            },
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount_due"] == 300.0
        assert data["data"]["discount_applied"] == 0.0

    def test_enroll_student_student_not_found(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": 99999, "group_id": group.id},
        )

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_enroll_student_group_not_found(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_student
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": student.id, "group_id": 99999},
        )

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_enroll_student_duplicate(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        create_test_enrollment(db_session, student_id=student.id, group_id=group.id, status="active")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": student.id, "group_id": group.id, "amount_due": 100.0},
        )

        assert response.status_code == 409, response.text
        data = response.json()
        assert data["success"] is False

    def test_enroll_student_unauthorized(self, client):
        response = client.post(
            "/api/v1/enrollments",
            json={"student_id": 1, "group_id": 1},
        )
        assert response.status_code == 401

    def test_enroll_student_validation_error(self, client, mock_admin_headers, override_auth):
        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": "not-an-int"},
        )
        assert response.status_code == 422, response.text
        data = response.json()
        assert data["success"] is False


class TestEnrollmentUpdate:
    """PATCH /api/v1/enrollments/{enrollment_id} — Update enrollment details."""

    def test_update_enrollment_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id, amount_due=500.0)
        db_session.commit()

        response = client.patch(
            f"/api/v1/enrollments/{enrollment.id}",
            headers=mock_admin_headers,
            json={"amount_due": 400.0, "notes": "Updated notes"},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount_due"] == 400.0
        assert data["data"]["notes"] == "Updated notes"

    def test_update_enrollment_not_found(self, client, mock_admin_headers, override_auth):
        response = client.patch(
            "/api/v1/enrollments/99999",
            headers=mock_admin_headers,
            json={"amount_due": 100.0},
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_update_enrollment_dropped(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id, status="dropped")
        db_session.commit()

        response = client.patch(
            f"/api/v1/enrollments/{enrollment.id}",
            headers=mock_admin_headers,
            json={"amount_due": 100.0},
        )
        assert response.status_code in (400, 409), response.text
        data = response.json()
        assert data["success"] is False

    def test_update_enrollment_unauthorized(self, client, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id)
        db_session.commit()

        response = client.patch(
            f"/api/v1/enrollments/{enrollment.id}",
            json={"amount_due": 100.0},
        )
        assert response.status_code == 401

    def test_update_enrollment_validation_error(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id)
        db_session.commit()

        response = client.patch(
            f"/api/v1/enrollments/{enrollment.id}",
            headers=mock_admin_headers,
            json={"amount_due": -50.0},
        )
        assert response.status_code == 409, response.text
        data = response.json()
        assert data["success"] is False


class TestEnrollmentDrop:
    """DELETE /api/v1/enrollments/{enrollment_id} — Drop/destroy enrollment."""

    def test_drop_enrollment_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id)
        db_session.commit()

        response = client.delete(
            f"/api/v1/enrollments/{enrollment.id}?reason=Student%20left%20the%20program",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "dropped"
        assert "dropped" in data["message"].lower()

    def test_drop_enrollment_not_found(self, client, mock_admin_headers, override_auth):
        response = client.delete(
            "/api/v1/enrollments/99999",
            headers=mock_admin_headers,
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_drop_enrollment_unauthorized(self, client, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id)
        db_session.commit()

        response = client.delete(f"/api/v1/enrollments/{enrollment.id}")
        assert response.status_code == 401


class TestEnrollmentTransfer:
    """POST /api/v1/enrollments/transfer — Transfer student between groups."""

    def test_transfer_student_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group_a = create_test_group(db_session, course_id=course.id, instructor_id=emp.id, name=f"GroupA-{uuid4().hex[:8]}")
        group_b = create_test_group(db_session, course_id=course.id, instructor_id=emp.id, name=f"GroupB-{uuid4().hex[:8]}")
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group_a.id, status="active")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=mock_admin_headers,
            json={
                "from_enrollment_id": enrollment.id,
                "to_group_id": group_b.id,
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["group_id"] == group_b.id
        assert data["data"]["student_id"] == student.id

    def test_transfer_student_not_found(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=mock_admin_headers,
            json={"from_enrollment_id": 99999, "to_group_id": group.id},
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_transfer_student_group_not_found(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id)
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=mock_admin_headers,
            json={"from_enrollment_id": enrollment.id, "to_group_id": 99999},
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_transfer_student_unauthorized(self, client):
        response = client.post(
            "/api/v1/enrollments/transfer",
            json={"from_enrollment_id": 1, "to_group_id": 1},
        )
        assert response.status_code == 401


class TestEnrollmentRead:
    """GET endpoints — student history & group summary."""

    def test_get_student_enrollments_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id)
        db_session.commit()

        response = client.get(
            f"/api/v1/enrollments/student/{student.id}",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1
        assert data["data"][0]["student_id"] == student.id

    def test_get_student_enrollments_empty(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_student
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        db_session.commit()

        response = client.get(
            f"/api/v1/enrollments/student/{student.id}",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_student_enrollments_unauthorized(self, client, db_session):
        from tests.utils.db_helpers import create_test_student
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        db_session.commit()

        response = client.get(f"/api/v1/enrollments/student/{student.id}")
        assert response.status_code == 401

    def test_get_group_summary_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_student_with_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        _, student_a, _ = create_student_with_enrollment(
            db_session, group_id=group.id,
            student_name=f"StudentA-{uuid4().hex[:8]}",
            amount_due=500.0,
        )
        _, student_b, _ = create_student_with_enrollment(
            db_session, group_id=group.id,
            student_name=f"StudentB-{uuid4().hex[:8]}",
            amount_due=600.0,
        )
        db_session.commit()

        response = client.get(
            f"/api/v1/enrollments/group/{group.id}/students-summary",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2
        student_ids = {s["student_id"] for s in data["data"]}
        assert student_a.id in student_ids
        assert student_b.id in student_ids

    def test_get_group_summary_filter_level(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_student_with_enrollment, create_test_enrollment, create_test_student, create_test_parent
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        parent = create_test_parent(db_session, full_name=f"Parent-{uuid4().hex[:8]}")
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}", parent_id=parent.id)
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group.id, level_number=2)
        db_session.commit()

        response = client.get(
            f"/api/v1/enrollments/group/{group.id}/students-summary?level=2",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert data["data"][0]["level_number"] == 2

    def test_get_group_summary_unauthorized(self, client, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        db_session.commit()

        response = client.get(f"/api/v1/enrollments/group/{group.id}/students-summary")
        assert response.status_code == 401


class TestEnrollmentDiscount:
    """POST /api/v1/enrollments/{enrollment_id}/discount — Apply sibling discount."""

    def test_apply_discount_success(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_student_with_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        _, _, enrollment = create_student_with_enrollment(
            db_session, group_id=group.id,
            student_name=f"Student-{uuid4().hex[:8]}",
            amount_due=500.0,
        )
        db_session.commit()

        response = client.post(
            f"/api/v1/enrollments/{enrollment.id}/discount?discount_amount=50.0",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["discount_applied"] >= 50.0
        assert "discount" in data["message"].lower()

    def test_apply_discount_custom_amount(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_student_with_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        _, _, enrollment = create_student_with_enrollment(
            db_session, group_id=group.id,
            student_name=f"Student-{uuid4().hex[:8]}",
            amount_due=1000.0,
        )
        db_session.commit()

        response = client.post(
            f"/api/v1/enrollments/{enrollment.id}/discount?discount_amount=100.0",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["data"]["discount_applied"] >= 100.0

    def test_apply_discount_not_found(self, client, mock_admin_headers, override_auth):
        response = client.post(
            "/api/v1/enrollments/99999/discount?discount_amount=50.0",
            headers=mock_admin_headers,
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"

    def test_apply_discount_unauthorized(self, client, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_student_with_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        _, _, enrollment = create_student_with_enrollment(
            db_session, group_id=group.id,
            student_name=f"Student-{uuid4().hex[:8]}",
        )
        db_session.commit()

        response = client.post(f"/api/v1/enrollments/{enrollment.id}/discount?discount_amount=25.0")
        assert response.status_code == 401


class TestEnrollmentEdgeCases:
    """Edge cases and complex workflows."""

    def test_enroll_student_group_capacity(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id, max_capacity=1)
        student_a = create_test_student(db_session, full_name=f"StudentA-{uuid4().hex[:8]}")
        db_session.commit()

        # First enrollment fills the capacity
        resp1 = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": student_a.id, "group_id": group.id, "amount_due": 200.0},
        )
        assert resp1.status_code == 201

        student_b = create_test_student(db_session, full_name=f"StudentB-{uuid4().hex[:8]}")
        db_session.commit()

        resp2 = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": student_b.id, "group_id": group.id, "amount_due": 200.0},
        )
        data = resp2.json()
        assert data["success"] is True
        if "capacity" in data["message"].lower():
            assert "warning" in data["message"].lower() or "exceeded" in data["message"].lower()

    def test_enroll_student_system_admin(self, client, mock_admin_headers, override_system_admin_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group = create_test_group(db_session, course_id=course.id, instructor_id=emp.id)
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments",
            headers=mock_admin_headers,
            json={"student_id": student.id, "group_id": group.id, "amount_due": 150.0},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["success"] is True

    def test_full_transfer_workflow(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_employee, create_test_student, create_test_enrollment
        course = create_test_course(db_session, name=f"Course-{uuid4().hex[:8]}")
        emp = create_test_employee(db_session, full_name=f"Instr-{uuid4().hex[:8]}")
        group_a = create_test_group(db_session, course_id=course.id, instructor_id=emp.id, name=f"Origin-{uuid4().hex[:8]}")
        group_b = create_test_group(db_session, course_id=course.id, instructor_id=emp.id, name=f"Target-{uuid4().hex[:8]}")
        student = create_test_student(db_session, full_name=f"Student-{uuid4().hex[:8]}")
        enrollment = create_test_enrollment(db_session, student_id=student.id, group_id=group_a.id, status="active")
        db_session.commit()

        response = client.post(
            "/api/v1/enrollments/transfer",
            headers=mock_admin_headers,
            json={
                "from_enrollment_id": enrollment.id,
                "to_group_id": group_b.id,
            },
        )
        assert response.status_code == 200, response.text
        new_enrollment_id = response.json()["data"]["id"]

        # Original enrollment should now be 'transferred'
        history_resp = client.get(
            f"/api/v1/enrollments/student/{student.id}",
            headers=mock_admin_headers,
        )
        assert history_resp.status_code == 200
        enrollments = history_resp.json()["data"]
        old = [e for e in enrollments if e["id"] == enrollment.id]
        new = [e for e in enrollments if e["id"] == new_enrollment_id]
        assert len(old) == 1, "Original enrollment not found in history"
        assert old[0]["status"] == "transferred"
        assert len(new) == 1, "New enrollment not found in history"
        assert new[0]["status"] == "active"
        assert new[0]["group_id"] == group_b.id
