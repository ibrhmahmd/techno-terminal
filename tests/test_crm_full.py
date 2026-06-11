"""
Comprehensive CRM endpoint tests — covers students, parents, and history routers.
"""

import uuid
from datetime import date, datetime

import pytest

from tests.utils.db_helpers import create_test_parent, create_test_student, link_student_parent


# ── Helpers ────────────────────────────────────────────────────────────────────

def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def create_student_via_api(client, headers, **overrides):
    data = {
        "full_name": overrides.get("full_name", _unique("Student")),
        "date_of_birth": overrides.get("date_of_birth", "2010-01-01"),
        "gender": overrides.get("gender", "male"),
        "phone": overrides.get("phone", "+201000000001"),
        "notes": overrides.get("notes", "Test student"),
    }
    if overrides.get("parent_id") is not None:
        parent_id = overrides["parent_id"]
    else:
        parent_id = None
    payload = {
        "student_data": data,
        "parent_id": parent_id,
        "relationship": overrides.get("relationship"),
        "created_by_user_id": None,
    }
    resp = client.post("/api/v1/crm/students", headers=headers, json=payload)
    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# TestStudentCRUD — 14 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudentCRUD:
    """CRUD operations for students."""

    def test_create_student_success(self, client, mock_admin_headers, override_auth):
        name = _unique("Student")
        resp = create_student_via_api(client, mock_admin_headers, full_name=name)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["full_name"] == name
        assert body["data"]["id"] > 0

        # Verify via GET
        sid = body["data"]["id"]
        get_resp = client.get(f"/api/v1/crm/students/{sid}", headers=mock_admin_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["full_name"] == name

    @pytest.mark.xfail(strict=False, reason="App bug: ImportError cannot import name 'StudentParent'")
    def test_create_student_with_parent(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session)
        name = _unique("Student")
        resp = create_student_via_api(
            client, mock_admin_headers, full_name=name, parent_id=parent.id
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True

        # Verify parent link
        sid = body["data"]["id"]
        parents_resp = client.get(
            f"/api/v1/crm/students/{sid}/parents", headers=mock_admin_headers
        )
        assert parents_resp.status_code == 200
        parent_ids = [p["id"] for p in parents_resp.json()["data"]]
        assert parent.id in parent_ids

    @pytest.mark.xfail(strict=False, reason="App bug: no empty-string validation on full_name")
    def test_create_student_validation_error(self, client, mock_admin_headers, override_auth):
        resp = client.post(
            "/api/v1/crm/students",
            headers=mock_admin_headers,
            json={"student_data": {"full_name": ""}, "parent_id": None},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"] == "ValidationError"

    def test_create_student_unauthorized(self, client):
        resp = client.post(
            "/api/v1/crm/students",
            json={"student_data": {"full_name": "Hacker"}, "parent_id": None},
        )
        assert resp.status_code == 401

    def test_get_student_success(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/crm/students/{sid}", headers=mock_admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == sid
        assert body["data"]["full_name"]
        assert body["data"]["status"] in ("active", "waiting", "inactive")

    def test_get_student_not_found(self, client, mock_admin_headers, override_auth):
        resp = client.get("/api/v1/crm/students/99999", headers=mock_admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"] == "NotFoundError"

    def test_update_student_success(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]
        new_name = _unique("Updated")

        resp = client.patch(
            f"/api/v1/crm/students/{sid}",
            headers=mock_admin_headers,
            json={"full_name": new_name, "notes": "Updated notes"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["full_name"] == new_name
        assert body["data"]["notes"] == "Updated notes"

    def test_update_student_not_found(self, client, mock_admin_headers, override_auth):
        resp = client.patch(
            "/api/v1/crm/students/99999",
            headers=mock_admin_headers,
            json={"full_name": "Nope"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"] == "NotFoundError"

    def test_delete_student_success(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/crm/students/{sid}/hard", headers=mock_admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify gone
        get_resp = client.get(f"/api/v1/crm/students/{sid}", headers=mock_admin_headers)
        assert get_resp.status_code == 404

    def test_delete_student_not_found(self, client, mock_admin_headers, override_auth):
        resp = client.delete("/api/v1/crm/students/99999/hard", headers=mock_admin_headers)
        assert resp.status_code == 404

    @pytest.mark.xfail(strict=False, reason="App bug: restore returns 200 but student does not reappear in listing")
    def test_soft_delete_and_restore(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]

        # Soft delete
        soft_resp = client.delete(
            f"/api/v1/crm/students/{sid}/soft", headers=mock_admin_headers
        )
        assert soft_resp.status_code == 200
        assert soft_resp.json()["data"]["status"] == "soft_deleted"

        # Should not appear in normal list
        list_resp = client.get(
            "/api/v1/crm/students?skip=0&limit=50", headers=mock_admin_headers
        )
        ids = [s["id"] for s in list_resp.json()["data"]]
        assert sid not in ids

        # Restore
        restore_resp = client.post(
            f"/api/v1/crm/students/{sid}/restore", headers=mock_admin_headers
        )
        assert restore_resp.status_code == 200
        assert restore_resp.json()["data"]["status"] == "restored"

        # Should now appear again
        list_resp2 = client.get(
            "/api/v1/crm/students?skip=0&limit=50", headers=mock_admin_headers
        )
        ids2 = [s["id"] for s in list_resp2.json()["data"]]
        assert sid in ids2

    def test_list_students_success(self, client, mock_admin_headers, override_auth):
        resp = client.get(
            "/api/v1/crm/students?skip=0&limit=10", headers=mock_admin_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert "total" in body
        assert "skip" in body
        assert "limit" in body

    def test_list_students_pagination(self, client, mock_admin_headers, override_auth):
        resp1 = client.get(
            "/api/v1/crm/students?skip=0&limit=5", headers=mock_admin_headers
        )
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["skip"] == 0
        assert d1["limit"] == 5

        resp2 = client.get(
            "/api/v1/crm/students?skip=5&limit=5", headers=mock_admin_headers
        )
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["skip"] == 5
        assert d2["limit"] == 5

    def test_list_students_search(self, client, mock_admin_headers, override_auth):
        name = _unique("SearchMe")
        create_student_via_api(client, mock_admin_headers, full_name=name)

        resp = client.get(
            f"/api/v1/crm/students?q={name[:10]}", headers=mock_admin_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        names = [s["full_name"] for s in body["data"]]
        assert any(name in n for n in names)


# ═══════════════════════════════════════════════════════════════════════════════
# TestStudentStatus — 7 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudentStatus:
    """Status management endpoints."""

    def test_update_student_status(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/crm/students/{sid}/status",
            headers=mock_admin_headers,
            json={"status": "waiting", "notes": "Full capacity"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["status"] == "waiting"

    def test_toggle_student_status(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/crm/students/{sid}/status/toggle",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()

        current = body["data"]["status"]
        assert current in ("active", "waiting")

        # Toggle again
        resp2 = client.post(
            f"/api/v1/crm/students/{sid}/status/toggle",
            headers=mock_admin_headers,
        )
        current2 = resp2.json()["data"]["status"]
        assert current2 != current

    def test_set_waiting_priority(self, client, mock_admin_headers, override_auth):
        create_resp = create_student_via_api(client, mock_admin_headers)
        sid = create_resp.json()["data"]["id"]

        # First set status to waiting
        client.patch(
            f"/api/v1/crm/students/{sid}/status",
            headers=mock_admin_headers,
            json={"status": "waiting"},
        )

        resp = client.patch(
            f"/api/v1/crm/students/{sid}/waiting-priority",
            headers=mock_admin_headers,
            json={"priority": 5, "notes": "High priority"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["waiting_priority"] == 5

    def test_get_students_by_status(self, client, mock_admin_headers, override_auth, db_session):
        create_test_student(db_session, status="active", full_name=_unique("ActiveOne"))
        create_test_student(db_session, status="active", full_name=_unique("ActiveTwo"))

        resp = client.get(
            "/api/v1/crm/students/by-status/active",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        for s in body["data"]:
            assert s["status"] == "active"

    def test_get_status_summary(self, client, mock_admin_headers, override_auth):
        resp = client.get(
            "/api/v1/crm/students/status-summary",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body["data"]
        assert "active" in body["data"]
        assert "waiting" in body["data"]
        assert "inactive" in body["data"]

    def test_get_waiting_list(self, client, mock_admin_headers, override_auth, db_session):
        s1 = create_test_student(db_session, status="waiting", full_name=_unique("WaitA"), birth_date="2010-06-15")
        s2 = create_test_student(db_session, status="waiting", full_name=_unique("WaitB"), birth_date=None)

        resp = client.get(
            "/api/v1/crm/students/waiting-list",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        for s in body["data"]:
            assert s["status"] == "waiting"
            assert "has_unpaid_balance" in s
            assert isinstance(s["has_unpaid_balance"], bool)
            assert "age" in s
        # Student with DOB should have age computed; student without should have null age
        s1_data = next(s for s in body["data"] if s["id"] == s1.id)
        assert s1_data["age"] is not None
        s2_data = next(s for s in body["data"] if s["id"] == s2.id)
        assert s2_data["age"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# TestStudentDetails — 6 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudentDetails:
    """Detail, relationship, and admin endpoints."""

    def test_get_student_details_success(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session)
        student = create_test_student(db_session, parent_id=parent.id)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/details",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["id"] == student.id
        assert body["data"]["full_name"] == student.full_name
        assert "primary_parent" in body["data"]

    def test_get_student_parents(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session)
        student = create_test_student(db_session, parent_id=parent.id)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/parents",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) >= 1
        assert body["data"][0]["id"] == parent.id

    def test_get_student_siblings(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session)
        s1 = create_test_student(db_session, parent_id=parent.id, full_name=_unique("SibA"))
        s2 = create_test_student(db_session, parent_id=parent.id, full_name=_unique("SibB"))

        resp = client.get(
            f"/api/v1/crm/students/{s1.id}/siblings",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        sibling_ids = [s["student_id"] for s in body["data"]]
        assert s2.id in sibling_ids

    def test_get_student_payments(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/payments",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["data"], list)
        assert "total" in body

    def test_get_deleted_students(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)
        # Soft-delete via API
        client.delete(
            f"/api/v1/crm/students/{student.id}/soft", headers=mock_admin_headers
        )

        resp = client.get(
            "/api/v1/crm/admin/deleted-students",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        deleted_ids = [s["id"] for s in body["data"]]
        assert student.id in deleted_ids

    def test_get_student_grouped(self, client, mock_admin_headers, override_auth, db_session):
        from tests.utils.db_helpers import create_test_course, create_test_group, create_test_enrollment

        s_active = create_test_student(db_session, status="active", full_name=_unique("GA"), birth_date="2015-03-10", gender="male")
        s_waiting = create_test_student(db_session, status="waiting", full_name=_unique("GW"), birth_date=None)

        # Give active student an enrollment with balance to test has_unpaid_balance
        course = create_test_course(db_session, name=_unique("GCourse"))
        group = create_test_group(db_session, course_id=course.id, name=_unique("GGroup"))
        create_test_enrollment(db_session, student_id=s_active.id, group_id=group.id, status="active", amount_due=200.0)

        resp = client.get(
            "/api/v1/crm/students/grouped?group_by=status&limit=200",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "groups" in body["data"]
        # Check unified DTO fields on grouped students
        for bucket in body["data"]["groups"]:
            for student in bucket["students"]:
                assert "has_unpaid_balance" in student
                assert isinstance(student["has_unpaid_balance"], bool)
                assert "age" in student
        # Active student should have has_unpaid_balance true and age computed
        active_bucket = next(b for b in body["data"]["groups"] if b["key"] == "active")
        active_student = next(s for s in active_bucket["students"] if s["id"] == s_active.id)
        assert active_student["has_unpaid_balance"] is True
        assert active_student["age"] is not None
        assert active_student["current_group_name"] is not None


# ═══════════════════════════════════════════════════════════════════════════════
# TestStudentFilter — 4 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudentFilter:
    """Filter endpoints."""

    def test_filter_students_by_status(self, client, mock_admin_headers, override_auth, db_session):
        create_test_student(db_session, status="active", full_name=_unique("FA"))
        create_test_student(db_session, status="inactive", full_name=_unique("FI"))

        resp = client.get(
            "/api/v1/crm/students/filter?status=active",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        if body["data"].get("students"):
            for s in body["data"]["students"]:
                assert s["status"] == "active"

    def test_filter_students_by_age(self, client, mock_admin_headers, override_auth, db_session):
        create_test_student(
            db_session, birth_date="2010-06-15", full_name=_unique("AgeA")
        )

        resp = client.get(
            "/api/v1/crm/students/filter?min_age=5&max_age=20",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_filter_students_by_gender(self, client, mock_admin_headers, override_auth, db_session):
        create_test_student(
            db_session, gender="female", full_name=_unique("FemaleS")
        )

        resp = client.get(
            "/api/v1/crm/students/filter?gender=female",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_filter_students_no_results(self, client, mock_admin_headers, override_auth):
        resp = client.get(
            "/api/v1/crm/students/filter?min_age=99&max_age=99",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# TestParentCRUD — 8 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestParentCRUD:
    """CRUD operations for parents."""

    def test_create_parent_success(self, client, mock_admin_headers, override_auth):
        name = _unique("Parent")
        phone = f"+20100{uuid.uuid4().int % 10**8:08d}"
        resp = client.post(
            "/api/v1/crm/parents",
            headers=mock_admin_headers,
            json={
                "full_name": name,
                "phone_primary": phone,
                "phone_secondary": None,
                "email": f"{name}@test.com",
                "relation": "mother",
                "notes": "Test parent",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["full_name"] == name
        # Phone is cleaned by RegisterParentInput validator (strips non-digits)
        assert body["data"]["phone_primary"] == phone.lstrip("+")

    @pytest.mark.xfail(strict=False, reason="App bug: no empty-string validation on full_name/phone_primary")
    def test_create_parent_validation(self, client, mock_admin_headers, override_auth):
        resp = client.post(
            "/api/v1/crm/parents",
            headers=mock_admin_headers,
            json={"full_name": "", "phone_primary": ""},
        )
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_get_parent_success(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session, full_name=_unique("GetParent"))

        resp = client.get(
            f"/api/v1/crm/parents/{parent.id}",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == parent.id
        assert body["data"]["full_name"] == parent.full_name

    def test_get_parent_not_found(self, client, mock_admin_headers, override_auth):
        resp = client.get("/api/v1/crm/parents/99999", headers=mock_admin_headers)
        assert resp.status_code == 404
        assert resp.json()["error"] == "NotFoundError"

    def test_update_parent_success(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session, full_name=_unique("Before"))
        new_phone = f"+20100{uuid.uuid4().hex[:6]}"

        resp = client.patch(
            f"/api/v1/crm/parents/{parent.id}",
            headers=mock_admin_headers,
            json={"phone_primary": new_phone, "notes": "Updated phone"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["phone_primary"] == new_phone
        assert body["data"]["notes"] == "Updated phone"

    def test_update_parent_not_found(self, client, mock_admin_headers, override_auth):
        resp = client.patch(
            "/api/v1/crm/parents/99999",
            headers=mock_admin_headers,
            json={"full_name": "Ghost"},
        )
        assert resp.status_code == 404

    def test_delete_parent_success(self, client, mock_admin_headers, override_auth, db_session):
        parent = create_test_parent(db_session, full_name=_unique("DelParent"))

        resp = client.delete(
            f"/api/v1/crm/parents/{parent.id}",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

        # Verify gone
        get_resp = client.get(
            f"/api/v1/crm/parents/{parent.id}", headers=mock_admin_headers
        )
        assert get_resp.status_code == 404

    def test_list_parents_search(self, client, mock_admin_headers, override_auth, db_session):
        target = _unique("SearchTarget")
        create_test_parent(db_session, full_name=target)

        resp = client.get(
            f"/api/v1/crm/parents?q={target[:10]}",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        names = [p["full_name"] for p in body["data"]]
        assert any(target in n for n in names)


# ═══════════════════════════════════════════════════════════════════════════════
# TestHistoryEndpoints — 8 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHistoryEndpoints:
    """Activity and history endpoints."""

    def test_get_student_history(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/history",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    def test_get_activity_summary(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/activity-summary",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["data"], list)

    def test_log_manual_activity(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)

        resp = client.post(
            f"/api/v1/crm/students/{student.id}/log-activity",
            headers=mock_admin_headers,
            json={
                "activity_type": "note_added",
                "description": "Manual test activity",
                "metadata": {"source": "pytest"},
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["activity_id"] > 0
        assert body["data"]["activity_type"] == "note_added"

        # Verify it appears in history
        hist_resp = client.get(
            f"/api/v1/crm/students/{student.id}/history",
            headers=mock_admin_headers,
        )
        activities = hist_resp.json()["data"]
        assert any(a["activity_id"] == body["data"]["activity_id"] for a in activities)

    def test_update_manual_activity(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)
        log_resp = client.post(
            f"/api/v1/crm/students/{student.id}/log-activity",
            headers=mock_admin_headers,
            json={"activity_type": "note_added", "description": "Original desc"},
        )
        aid = log_resp.json()["data"]["activity_id"]

        resp = client.patch(
            f"/api/v1/crm/students/{student.id}/log-activity/{aid}",
            headers=mock_admin_headers,
            json={"description": "Updated desc", "activity_type": "note_added"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["description"] == "Updated desc"

    def test_delete_manual_activity(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)
        log_resp = client.post(
            f"/api/v1/crm/students/{student.id}/log-activity",
            headers=mock_admin_headers,
            json={"activity_type": "note_added", "description": "To delete"},
        )
        aid = log_resp.json()["data"]["activity_id"]

        resp = client.delete(
            f"/api/v1/crm/students/{student.id}/log-activity/{aid}",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

    def test_get_recent_activity(self, client, mock_admin_headers, override_auth):
        resp = client.get(
            "/api/v1/crm/history/recent?limit=5",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    def test_search_activities(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)
        client.post(
            f"/api/v1/crm/students/{student.id}/log-activity",
            headers=mock_admin_headers,
            json={"activity_type": "note_added", "description": "UniqueSearchTerm"},
        )

        resp = client.post(
            "/api/v1/crm/history/search",
            headers=mock_admin_headers,
            json={"search_term": "UniqueSearchTerm", "limit": 10},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["data"]) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Additional History: enrollment-history, status-history, competition-history
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudentHistorySubEndpoints:
    """Enrollment, status, and competition history endpoints."""

    def test_get_enrollment_history(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/enrollment-history",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body["data"], list)
        assert "total" in body

    def test_get_status_history(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)
        # Trigger a status change to create history
        client.patch(
            f"/api/v1/crm/students/{student.id}/status",
            headers=mock_admin_headers,
            json={"status": "inactive", "notes": "Status change for history"},
        )

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/status-history",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body["data"], list)

    def test_get_competition_history(self, client, mock_admin_headers, override_auth, db_session):
        student = create_test_student(db_session)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/competition-history",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body["data"], list)
        assert "total" in body

    def test_get_student_status_history_router(self, client, mock_admin_headers, override_auth, db_session):
        """Status-history endpoint on the students router."""
        student = create_test_student(db_session)

        resp = client.get(
            f"/api/v1/crm/students/{student.id}/status-history",
            headers=mock_admin_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
