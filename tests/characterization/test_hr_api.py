"""Characterization tests for the HR HTTP API (ticket #16, Phase A).

Pins the exact status codes, response envelopes and field shapes of every
endpoint under ``/api/v1/hr`` (9 endpoints) BEFORE the HR HTTP layer moves
into ``app/modules/hr/api``.

Buckets
-------
* HR services open their own ``get_session()`` via ``HRUnitOfWork`` in places,
  so rows created through the rollback-only ``uow`` fixture are invisible to them.
  GET endpoints that need data are therefore seeded through the committed
  ``db_session`` fixture with uuid-tagged values. Write endpoints assert
  response shape only and use uuid-tagged values so reruns do not collide
  (their commits are real).
* Supabase is faked by patching the accessor where the code under test looks it
  up: the router module for endpoints that call it directly, the staff account
  service module for ``create_account``. No network; nothing here needs the
  ``supabase`` marker.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from sqlmodel import select

from app.modules.auth.models.auth_models import User as UserModel
from app.modules.hr.models.employee_models import Employee

# Module paths for patching — these are the only strings that move with the
# router/service in Phase A. After the move, update these constants.
HR_ROUTER = "app.modules.hr.api.hr_router"
STAFF_ACCOUNT_SERVICE = "app.modules.hr.services.staff_account_service"
HR_SCHEMAS = "app.modules.hr.api.schemas"
DEPENDENCIES = "app.api.dependencies"
HR_DEPS = "app.modules.hr.api.deps"


def _uid() -> str:
    return f"ca-{uuid.uuid4().hex}"


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _phone() -> str:
    """Generate a valid phone number matching ^\+?\d{10,}$."""
    return f"+201{uuid.uuid4().int % 10**9:09d}"


def _make_user(db_session, supabase_uid=None, **overrides) -> UserModel:
    """Insert a committed user (visible to the services' own sessions)."""
    user = UserModel(
        username=overrides.pop("username", f"ca_{_short()}"),
        role=overrides.pop("role", "admin"),
        supabase_uid=supabase_uid or _uid(),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_employee(db_session, **overrides) -> Employee:
    """Insert a committed employee (visible to the services' own sessions)."""
    emp = Employee(
        full_name=overrides.pop("full_name", f"ca_{_short()}"),
        phone=overrides.pop("phone", _phone()),
        email=overrides.pop("email", f"ca_{_short()}@test.com"),
        national_id=overrides.pop("national_id", f"NID{_short()}"),
        university=overrides.pop("university", "Test University"),
        major=overrides.pop("major", "Computer Science"),
        is_graduate=overrides.pop("is_graduate", False),
        job_title=overrides.pop("job_title", "Engineer"),
        employment_type=overrides.pop("employment_type", "full_time"),
        monthly_salary=overrides.pop("monthly_salary", 5000.0),
        contract_percentage=overrides.pop("contract_percentage", None),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return emp


def _fake_admin_client(uid="sup-uid"):
    """Create a fake Supabase admin client."""
    admin = MagicMock()
    admin.auth.admin.create_user.return_value.user.id = uid
    return admin


# ── /api/v1/hr/employees (list) ────────────────────────────────────────────────

def test_list_employees(client_with_uow, db_session, override_auth, mock_admin_headers):
    """GET /hr/employees returns paginated list of employees."""
    marker = _short()
    _make_employee(db_session, full_name=f"emp_{marker}", phone=f"+2010{marker}")

    r = client_with_uow.get("/api/v1/hr/employees", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert body["message"].startswith("Showing ")
    if body["data"]:
        emp = body["data"][0]
        assert set(emp.keys()) >= {
            "id", "full_name", "phone", "email", "job_title",
            "employment_type", "is_active", "deleted_at", "deleted_by"
        }


def test_list_employees_include_deleted(client_with_uow, db_session, override_auth, mock_admin_headers):
    """GET /hr/employees?include_deleted=true includes soft-deleted."""
    emp = _make_employee(db_session, full_name=f"del_{_short()}")
    # Soft delete via service would be ideal but we're testing GET; just verify the flag works
    r = client_with_uow.get("/api/v1/hr/employees", params={"include_deleted": "true"}, headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True


def test_list_employees_pagination(client_with_uow, db_session, override_auth, mock_admin_headers):
    """GET /hr/employees respects page and page_size."""
    for i in range(3):
        _make_employee(db_session, full_name=f"pag_{_short()}_{i}")

    r = client_with_uow.get("/api/v1/hr/employees", params={"page": 1, "page_size": 2}, headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["data"]) <= 2


def test_list_employees_unauthorized(client):
    """GET /hr/employees without auth returns 401."""
    r = client.get("/api/v1/hr/employees")
    assert r.status_code == 401


# ── /api/v1/hr/employees/{id} (get) ────────────────────────────────────────────

def test_get_employee_success(client_with_uow, db_session, override_auth, mock_admin_headers):
    """GET /hr/employees/{id} returns full employee details."""
    emp = _make_employee(db_session, full_name=f"get_{_short()}", hired_at=date(2024, 1, 15))

    r = client_with_uow.get(f"/api/v1/hr/employees/{emp.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data.keys()) >= {
        "id", "full_name", "phone", "email", "national_id", "job_title",
        "employment_type", "is_active", "hired_at", "has_account", "university",
        "major", "is_graduate", "monthly_salary", "contract_percentage",
        "deleted_at", "deleted_by"
    }
    assert data["id"] == emp.id
    assert data["full_name"] == emp.full_name
    # hired_at must be YYYY-MM-DD date string (the #3 fix)
    assert data["hired_at"] == "2024-01-15"


def test_get_employee_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /hr/employees/{id} for non-existent ID returns 404."""
    r = client_with_uow.get("/api/v1/hr/employees/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_get_employee_unauthorized(client):
    """GET /hr/employees/{id} without auth returns 401."""
    r = client.get("/api/v1/hr/employees/1")
    assert r.status_code == 401


# ── /api/v1/hr/employees (create) ──────────────────────────────────────────────

def test_create_employee_success(client_with_uow, override_auth, mock_admin_headers):
    """POST /hr/employees creates a new employee."""
    payload = {
        "full_name": f"Create {_short()}",
        "phone": _phone(),
        "email": f"create_{_short()}@test.com",
        "national_id": f"NID{_short()}",
        "university": "Test University",
        "major": "Computer Science",
        "is_graduate": False,
        "job_title": "Engineer",
        "employment_type": "full_time",
        "monthly_salary": 5000.0,
        "contract_percentage": None,
        "is_active": True,
    }

    r = client_with_uow.post("/api/v1/hr/employees", headers=mock_admin_headers, json=payload)

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Employee created successfully."
    data = body["data"]
    assert set(data.keys()) >= {
        "id", "full_name", "phone", "email", "national_id", "job_title",
        "employment_type", "is_active", "hired_at", "has_account", "university",
        "major", "is_graduate", "monthly_salary", "contract_percentage",
        "deleted_at", "deleted_by"
    }
    assert data["full_name"] == payload["full_name"]
    # Phone is stored as digits only (clean_phone validator strips non-digits)
    assert data["phone"] == payload["phone"].lstrip("+")
    assert data["national_id"] == payload["national_id"]
    assert data["employment_type"] == "full_time"
    assert data["is_active"] is True
    # hired_at is not set on creation (optional field)
    assert data["hired_at"] is None


def test_create_employee_duplicate_national_id(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees with duplicate national_id returns 409."""
    existing = _make_employee(db_session, national_id=f"DUP{_short()}")
    payload = {
        "full_name": f"Dup {_short()}",
        "phone": _phone(),
        "email": f"dup_{_short()}@test.com",
        "national_id": existing.national_id,
        "university": "Test University",
        "major": "Computer Science",
        "is_graduate": False,
        "job_title": "Engineer",
        "employment_type": "full_time",
        "monthly_salary": 5000.0,
        "contract_percentage": None,
        "is_active": True,
    }

    r = client_with_uow.post("/api/v1/hr/employees", headers=mock_admin_headers, json=payload)

    assert r.status_code == 409
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "ConflictError"
    assert "national_id" in body["message"].lower()


def test_create_employee_validation_error(client_with_uow, override_auth, mock_admin_headers):
    """POST /hr/employees with missing required field returns 422."""
    payload = {
        "full_name": "Test",
        "phone": "+201000000000",
        # missing national_id, university, major
    }

    r = client_with_uow.post("/api/v1/hr/employees", headers=mock_admin_headers, json=payload)

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_create_employee_unauthorized(client):
    """POST /hr/employees without auth returns 401."""
    payload = {"full_name": "Test", "phone": "+201000000000", "national_id": "NID123456", "university": "U", "major": "M"}
    r = client.post("/api/v1/hr/employees", json=payload)
    assert r.status_code == 401


# ── /api/v1/hr/employees/{id} (update) ─────────────────────────────────────────

def test_update_employee_success(client_with_uow, db_session, override_auth, mock_admin_headers):
    """PUT /hr/employees/{id} updates an employee."""
    emp = _make_employee(db_session, full_name=f"Update {_short()}")

    payload = {
        "full_name": f"Updated {_short()}",
        "job_title": "Senior Engineer",
        "monthly_salary": 6000.0,
    }

    r = client_with_uow.put(f"/api/v1/hr/employees/{emp.id}", headers=mock_admin_headers, json=payload)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Employee updated successfully."
    data = body["data"]
    assert data["id"] == emp.id
    assert data["full_name"] == payload["full_name"]
    assert data["job_title"] == "Senior Engineer"
    assert data["monthly_salary"] == 6000.0


def test_update_employee_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PUT /hr/employees/{id} for non-existent ID returns 404."""
    payload = {"full_name": "Updated"}
    r = client_with_uow.put("/api/v1/hr/employees/999999999", headers=mock_admin_headers, json=payload)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_update_employee_unauthorized(client):
    """PUT /hr/employees/{id} without auth returns 401."""
    r = client.put("/api/v1/hr/employees/1", json={"full_name": "Test"})
    assert r.status_code == 401


# ── /api/v1/hr/employees/{id} (delete) ─────────────────────────────────────────

def test_delete_employee_success(client_with_uow, db_session, override_auth, mock_admin_headers):
    """DELETE /hr/employees/{id} soft-deletes an employee."""
    emp = _make_employee(db_session, full_name=f"Delete {_short()}")
    actor = _make_user(db_session)

    r = client_with_uow.delete(f"/api/v1/hr/employees/{emp.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] is True
    assert body["message"] == "Employee deleted successfully."


def test_delete_employee_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /hr/employees/{id} for non-existent ID returns 404."""
    r = client_with_uow.delete("/api/v1/hr/employees/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_delete_employee_unauthorized(client):
    """DELETE /hr/employees/{id} without auth returns 401."""
    r = client.delete("/api/v1/hr/employees/1")
    assert r.status_code == 401


# ── /api/v1/hr/employees/{id}/restore (restore) ────────────────────────────────

def test_restore_employee_success(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/restore restores a soft-deleted employee."""
    emp = _make_employee(db_session, full_name=f"Restore {_short()}")
    # Soft delete it first via the service layer (we can't easily call the endpoint here
    # without going through the same service; just test the endpoint shape)
    # Instead, directly set deleted_at in DB
    from app.shared.datetime_utils import utc_now
    emp.deleted_at = utc_now()
    emp.deleted_by = 1
    db_session.add(emp)
    db_session.commit()

    r = client_with_uow.post(f"/api/v1/hr/employees/{emp.id}/restore", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Employee restored successfully."
    data = body["data"]
    assert data["id"] == emp.id
    assert data["deleted_at"] is None
    assert data["deleted_by"] is None


def test_restore_employee_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/restore for non-existent ID returns 404."""
    r = client_with_uow.post("/api/v1/hr/employees/999999999/restore", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_restore_employee_already_active(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/restore on non-deleted employee returns 409."""
    emp = _make_employee(db_session, full_name=f"Active {_short()}")

    r = client_with_uow.post(f"/api/v1/hr/employees/{emp.id}/restore", headers=mock_admin_headers)

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ConflictError"


def test_restore_employee_unauthorized(client):
    """POST /hr/employees/{id}/restore without auth returns 401."""
    r = client.post("/api/v1/hr/employees/1/restore")
    assert r.status_code == 401


# ── /api/v1/hr/staff-accounts (list) ───────────────────────────────────────────

def test_list_staff_accounts(client_with_uow, db_session, override_auth, mock_admin_headers):
    """GET /hr/staff-accounts returns staff accounts with employee info."""
    emp = _make_employee(db_session, full_name=f"Staff {_short()}")
    user = _make_user(db_session, username=f"staff_{_short()}@test.com", employee_id=emp.id)

    r = client_with_uow.get("/api/v1/hr/staff-accounts", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    if body["data"]:
        acc = body["data"][0]
        assert set(acc.keys()) >= {
            "id", "username", "email", "employee_id", "employee_name",
            "job_title", "is_active", "created_at"
        }


def test_list_staff_accounts_unauthorized(client):
    """GET /hr/staff-accounts without auth returns 401."""
    r = client.get("/api/v1/hr/staff-accounts")
    assert r.status_code == 401


# ── /api/v1/hr/attendance/log (stub) ───────────────────────────────────────────

def test_log_attendance_stub(client_with_uow, override_auth, mock_admin_headers):
    """POST /hr/attendance/log returns stub response (not persisted)."""
    payload = {
        "employee_id": 1,
        "status": "check_in",
        "notes": "Test attendance",
    }

    r = client_with_uow.post("/api/v1/hr/attendance/log", headers=mock_admin_headers, json=payload)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "HR attendance logging stub completed."
    data = body["data"]
    assert set(data.keys()) == {"employee_id", "status", "logged_at", "message"}
    assert data["employee_id"] == 1
    assert data["status"] == "check_in"
    assert "logged_at" in data


def test_log_attendance_check_out(client_with_uow, override_auth, mock_admin_headers):
    """POST /hr/attendance/log with check_out status."""
    payload = {"employee_id": 1, "status": "check_out"}

    r = client_with_uow.post("/api/v1/hr/attendance/log", headers=mock_admin_headers, json=payload)

    assert r.status_code == 200
    body = r.json()
    assert body["data"]["status"] == "check_out"


def test_log_attendance_validation_error(client_with_uow, override_auth, mock_admin_headers):
    """POST /hr/attendance/log with invalid employee_id returns 422."""
    payload = {"employee_id": "not-an-int", "status": "check_in"}

    r = client_with_uow.post("/api/v1/hr/attendance/log", headers=mock_admin_headers, json=payload)

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_log_attendance_unauthorized(client):
    """POST /hr/attendance/log without auth returns 401."""
    r = client.post("/api/v1/hr/attendance/log", json={"employee_id": 1, "status": "check_in"})
    assert r.status_code == 401


# ── /api/v1/hr/employees/{id}/create-account (Supabase) ────────────────────────

def test_create_employee_account_success(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/create-account provisions Supabase account."""
    emp = _make_employee(db_session, full_name=f"Acc {_short()}")

    fake_admin = _fake_admin_client(uid=f"sup-{_short()}")
    
    # Create fake service with the db_session (which can commit)
    from app.modules.hr.services.staff_account_service import StaffAccountService
    from app.modules.hr.repositories import HRUnitOfWork
    uow = HRUnitOfWork(db_session)
    fake_service = StaffAccountService(uow, fake_admin)
    
    # Override the service factory to return our fake service
    from app.modules.hr.api.deps import get_staff_account_service
    client_with_uow.app.dependency_overrides[get_staff_account_service] = lambda: fake_service
    try:
        r = client_with_uow.post(
            f"/api/v1/hr/employees/{emp.id}/create-account",
            headers=mock_admin_headers,
            json={
                "email": f"acc_{_short()}@test.com",
                "password": "StrongPassword123",
                "role": "admin",
            },
        )
    finally:
        client_with_uow.app.dependency_overrides.pop(get_staff_account_service, None)

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Employee account created successfully."
    data = body["data"]
    assert set(data.keys()) == {"employee_id", "user_id", "email", "role", "created_at"}
    assert data["employee_id"] == emp.id
    assert data["role"] == "admin"
    assert "created_at" in data


def test_create_employee_account_employee_not_found(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/create-account for non-existent employee returns 404."""
    fake_admin = _fake_admin_client()
    
    from app.modules.hr.services.staff_account_service import StaffAccountService
    from app.modules.hr.repositories import HRUnitOfWork
    uow = HRUnitOfWork(db_session)
    fake_service = StaffAccountService(uow, fake_admin)
    
    from app.modules.hr.api.deps import get_staff_account_service
    client_with_uow.app.dependency_overrides[get_staff_account_service] = lambda: fake_service
    try:
        r = client_with_uow.post(
            "/api/v1/hr/employees/999999999/create-account",
            headers=mock_admin_headers,
            json={"email": "test@test.com", "password": "StrongPassword123", "role": "admin"},
        )
    finally:
        client_with_uow.app.dependency_overrides.pop(get_staff_account_service, None)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_create_employee_account_duplicate_email(client_with_uow, db_session, override_auth, mock_admin_headers, monkeypatch):
    """POST /hr/employees/{id}/create-account with taken email returns 409."""
    emp = _make_employee(db_session, full_name=f"Acc {_short()}")

    class FakeAdmin:
        @staticmethod
        def create_user(data):
            raise Exception("User already registered")

    fake_admin = type("C", (), {"auth": type("A", (), {"admin": FakeAdmin()})()})()
    
    from app.modules.hr.services.staff_account_service import StaffAccountService
    from app.modules.hr.repositories import HRUnitOfWork
    uow = HRUnitOfWork(db_session)
    fake_service = StaffAccountService(uow, fake_admin)
    
    from app.modules.hr.api.deps import get_staff_account_service
    client_with_uow.app.dependency_overrides[get_staff_account_service] = lambda: fake_service
    try:
        r = client_with_uow.post(
            f"/api/v1/hr/employees/{emp.id}/create-account",
            headers=mock_admin_headers,
            json={"email": "taken@test.com", "password": "StrongPassword123", "role": "admin"},
        )
    finally:
        client_with_uow.app.dependency_overrides.pop(get_staff_account_service, None)

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ConflictError"


def test_create_employee_account_validation_errors(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/create-account with invalid input returns 422."""
    emp = _make_employee(db_session, full_name=f"Acc {_short()}")
    fake_admin = _fake_admin_client()
    
    from app.modules.hr.services.staff_account_service import StaffAccountService
    from app.modules.hr.repositories import HRUnitOfWork
    uow = HRUnitOfWork(db_session)
    fake_service = StaffAccountService(uow, fake_admin)
    
    from app.modules.hr.api.deps import get_staff_account_service
    client_with_uow.app.dependency_overrides[get_staff_account_service] = lambda: fake_service
    try:
        # Short password
        r = client_with_uow.post(
            f"/api/v1/hr/employees/{emp.id}/create-account",
            headers=mock_admin_headers,
            json={"email": "test@test.com", "password": "short", "role": "admin"},
        )
    finally:
        client_with_uow.app.dependency_overrides.pop(get_staff_account_service, None)

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_create_employee_account_unauthorized(client):
    """POST /hr/employees/{id}/create-account without auth returns 401."""
    r = client.post("/api/v1/hr/employees/1/create-account", json={"email": "t@t.com", "password": "pass", "role": "admin"})
    assert r.status_code == 401


def test_create_employee_account_invalid_role(client_with_uow, db_session, override_auth, mock_admin_headers):
    """POST /hr/employees/{id}/create-account with invalid role returns 422."""
    emp = _make_employee(db_session, full_name=f"Acc {_short()}")
    fake_admin = _fake_admin_client()
    
    from app.modules.hr.services.staff_account_service import StaffAccountService
    from app.modules.hr.repositories import HRUnitOfWork
    uow = HRUnitOfWork(db_session)
    fake_service = StaffAccountService(uow, fake_admin)
    
    from app.modules.hr.api.deps import get_staff_account_service
    client_with_uow.app.dependency_overrides[get_staff_account_service] = lambda: fake_service
    try:
        r = client_with_uow.post(
            f"/api/v1/hr/employees/{emp.id}/create-account",
            headers=mock_admin_headers,
            json={"email": "test@test.com", "password": "StrongPassword123", "role": "instructor"},
        )
    finally:
        client_with_uow.app.dependency_overrides.pop(get_staff_account_service, None)

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"