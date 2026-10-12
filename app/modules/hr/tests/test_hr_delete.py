"""Employee Soft Delete — lifecycle regression suite (feature 040).

US1: safe removal from every surface (lookup, lists, staff accounts,
login), actor-stamped markers, preserved history, uniform errors.
US3 tests live further down this module (restore & discovery).
"""
import uuid

from sqlmodel import select

from app.modules.auth.models.auth_models import User
from app.modules.hr.models.employee_models import Employee
from app.shared.datetime_utils import utc_now

BASE = "/api/v1/hr"


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _digits(n: int) -> str:
    return str(uuid.uuid4().int)[:n]


def valid_employee_payload(**overrides) -> dict:
    payload = {
        "full_name": f"Del Target {_digits(6)}",
        "phone": "01" + _digits(9),
        "email": f"{_unique()}@delete.test",
        "national_id": _digits(12),
        "university": "Cairo University",
        "major": "Computer Science",
        "is_graduate": False,
        "job_title": "Instructor",
        "employment_type": "full_time",
        "monthly_salary": None,
        "contract_percentage": None,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def _create_employee(client, headers: dict, **overrides) -> dict:
    resp = client.post(
        f"{BASE}/employees",
        json=valid_employee_payload(**overrides),
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


def _seed_linked_user(db_session, employee_id: int) -> User:
    """Create a local login and bind it 1:1 to the employee (both FK sides)."""
    tag = _unique()
    user = User(
        username=f"del-{tag}@staff.test",
        role="admin",
        supabase_uid=None,
        is_active=True,
        created_at=utc_now(),
    )
    db_session.add(user)
    db_session.flush()

    employee = db_session.get(Employee, employee_id)
    employee.user_id = user.id
    user.employee_id = employee_id
    db_session.add(employee)
    db_session.add(user)
    db_session.commit()
    return user


def _all_employee_ids(client, headers: dict) -> set[int]:
    """Collect every listed employee ID across all pages."""
    ids: set[int] = set()
    page = 1
    while True:
        resp = client.get(
            f"{BASE}/employees?page={page}&page_size=100", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        ids |= {item["id"] for item in data}
        if len(data) < 100:
            return ids
        page += 1


class TestDeleteLifecycle:
    def test_delete_stamps_markers_and_actor(
        self, client, mock_admin_headers, override_auth, db_session
    ):
        emp = _create_employee(client, mock_admin_headers)

        resp = client.delete(
            f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"] is True
        assert "deleted" in body["message"].lower()

        db_session.expire_all()
        row = db_session.get(Employee, emp["id"])
        assert row.deleted_at is not None

        acting_admin = db_session.exec(
            select(User).where(User.supabase_uid == "test-admin-001")
        ).first()
        assert row.deleted_by == acting_admin.id

        gone = client.get(
            f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
        )
        assert gone.status_code == 404
        assert gone.json()["error"] == "NotFoundError"

    def test_deleted_employee_hidden_from_list(
        self, client, mock_admin_headers, override_auth
    ):
        keep = _create_employee(client, mock_admin_headers)
        gone = _create_employee(client, mock_admin_headers)

        resp = client.delete(
            f"{BASE}/employees/{gone['id']}", headers=mock_admin_headers
        )
        assert resp.status_code == 200

        listed_ids = _all_employee_ids(client, mock_admin_headers)
        assert gone["id"] not in listed_ids
        assert keep["id"] in listed_ids

    def test_delete_blocks_linked_login_and_preserves_history(
        self, client, mock_admin_headers, override_auth, db_session
    ):
        emp = _create_employee(client, mock_admin_headers)
        user = _seed_linked_user(db_session, emp["id"])

        before = client.get(
            f"{BASE}/staff-accounts", headers=mock_admin_headers
        )
        assert before.status_code == 200
        assert any(
            acc["employee_id"] == emp["id"] for acc in before.json()["data"]
        )

        resp = client.delete(
            f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
        )
        assert resp.status_code == 200

        after = client.get(
            f"{BASE}/staff-accounts", headers=mock_admin_headers
        )
        assert after.status_code == 200
        assert not any(
            acc["employee_id"] == emp["id"] for acc in after.json()["data"]
        )

        db_session.expire_all()
        refreshed_user = db_session.get(User, user.id)
        assert refreshed_user.is_active is False
        assert refreshed_user.employee_id == emp["id"]

        refreshed_emp = db_session.get(Employee, emp["id"])
        assert refreshed_emp.user_id == user.id

    def test_double_delete_returns_uniform_404(
        self, client, mock_admin_headers, override_auth
    ):
        emp = _create_employee(client, mock_admin_headers)

        first = client.delete(
            f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
        )
        assert first.status_code == 200

        second = client.delete(
            f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
        )
        assert second.status_code == 404
        assert second.json()["error"] == "NotFoundError"

    def test_delete_requires_authentication(self, client):
        """Real dependency chain: no credentials must yield the standard 401."""
        resp = client.delete(f"{BASE}/employees/1")

        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert body["error"] == "Unauthorized"


class TestRestoreLifecycle:
    def test_restore_clears_markers_and_reveals_record(
        self, client, mock_admin_headers, override_auth, db_session
    ):
        emp = _create_employee(client, mock_admin_headers)
        user = _seed_linked_user(db_session, emp["id"])

        assert (
            client.delete(
                f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
            )
        ).status_code == 200

        resp = client.post(
            f"{BASE}/employees/{emp['id']}/restore",
            headers=mock_admin_headers,
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["id"] == emp["id"]
        assert data["deleted_at"] is None
        assert data["deleted_by"] is None

        refetched = client.get(
            f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
        )
        assert refetched.status_code == 200
        assert emp["id"] in _all_employee_ids(client, mock_admin_headers)

        db_session.expire_all()
        refreshed_user = db_session.get(User, user.id)
        assert refreshed_user.is_active is False

        overview = client.get(
            f"{BASE}/staff-accounts", headers=mock_admin_headers
        )
        assert any(
            acc["employee_id"] == emp["id"] for acc in overview.json()["data"]
        )

    def test_restore_of_live_employee_conflicts(
        self, client, mock_admin_headers, override_auth
    ):
        emp = _create_employee(client, mock_admin_headers)

        resp = client.post(
            f"{BASE}/employees/{emp['id']}/restore",
            headers=mock_admin_headers,
        )

        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["error"] == "ConflictError"
        assert "not deleted" in body["message"]

    def test_restore_of_unknown_id_not_found(
        self, client, mock_admin_headers, override_auth
    ):
        resp = client.post(
            f"{BASE}/employees/987654321/restore",
            headers=mock_admin_headers,
        )

        assert resp.status_code == 404
        assert resp.json()["error"] == "NotFoundError"

    def test_restore_after_rehire_reports_all_collisions(
        self, client, mock_admin_headers, override_auth
    ):
        identity = valid_employee_payload()
        original = _create_employee(
            client,
            mock_admin_headers,
            full_name=identity["full_name"],
            phone=identity["phone"],
            email=identity["email"],
            national_id=identity["national_id"],
        )
        assert (
            client.delete(
                f"{BASE}/employees/{original['id']}",
                headers=mock_admin_headers,
            )
        ).status_code == 200

        rehired = _create_employee(
            client,
            mock_admin_headers,
            full_name=identity["full_name"],
            phone=identity["phone"],
            email=identity["email"],
            national_id=identity["national_id"],
        )

        resp = client.post(
            f"{BASE}/employees/{original['id']}/restore",
            headers=mock_admin_headers,
        )

        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["error"] == "ConflictError"
        for field in ("national_id", "phone", "email"):
            assert field in body["message"]
        # The colliding live record must be untouched.
        still_there = client.get(
            f"{BASE}/employees/{rehired['id']}", headers=mock_admin_headers
        )
        assert still_there.status_code == 200


class TestIncludeDeletedFlag:
    def test_flag_reveals_deleted_rows_with_markers(
        self, client, mock_admin_headers, override_auth
    ):
        emp = _create_employee(client, mock_admin_headers)
        assert (
            client.delete(
                f"{BASE}/employees/{emp['id']}", headers=mock_admin_headers
            )
        ).status_code == 200

        default_ids = _all_employee_ids(client, mock_admin_headers)
        assert emp["id"] not in default_ids

        collected: dict = {}
        page = 1
        while emp["id"] not in collected:
            resp = client.get(
                f"{BASE}/employees?page={page}&page_size=100&include_deleted=true",
                headers=mock_admin_headers,
            )
            assert resp.status_code == 200
            data = resp.json()["data"]
            if not data:
                break
            collected = {item["id"]: item for item in data}
            page += 1

        assert emp["id"] in collected, "flagged listing must include the row"
        row = collected[emp["id"]]
        assert row["deleted_at"] is not None
        assert row["deleted_by"] is not None

    def test_flag_requires_authentication(self, client):
        resp = client.get(f"{BASE}/employees?include_deleted=true")

        assert resp.status_code == 401
        assert resp.json()["error"] == "Unauthorized"
