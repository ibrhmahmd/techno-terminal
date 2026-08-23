"""
Audit regression suite for feature 039-audit-employee-creation.

Test class names map 1:1 to findings IDs in specs/039-audit-employee-creation/findings.md
so SC-006 traceability holds: every ERROR-tier finding has ≥1 test here.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from tests.utils.db_helpers import create_test_employee


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def valid_employee_payload(**overrides):
    uid = uuid.uuid4().hex[:12]
    return {
        "full_name": overrides.get("full_name", _unique("Employee")),
        "phone": overrides.get("phone", f"010{str(uuid.uuid4().int)[:8]}"),
        "email": overrides.get("email", f"{uid}@test.com"),
        "national_id": overrides.get("national_id", uid.upper()),
        "university": overrides.get("university", "Cairo University"),
        "major": overrides.get("major", "Computer Science"),
        "is_graduate": overrides.get("is_graduate", False),
        "job_title": overrides.get("job_title", "Software Engineer"),
        "employment_type": overrides.get("employment_type", "full_time"),
        "monthly_salary": overrides.get("monthly_salary", 5000.0),
        "contract_percentage": overrides.get("contract_percentage", None),
        "is_active": overrides.get("is_active", True),
    }


def _create_employee(client, headers, **overrides):
    resp = client.post(
        "/api/v1/hr/employees", headers=headers, json=valid_employee_payload(**overrides)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


def _provision(client, headers, employee_id, email=None, password="Str0ngPass!23", role="admin"):
    return client.post(
        f"/api/v1/hr/employees/{employee_id}/create-account",
        headers=headers,
        json={
            "email": email or f"{_unique('acc')}@test.com",
            "password": password,
            "role": role,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# F-01 — Duplicate probes report EVERY colliding field at once
# ═══════════════════════════════════════════════════════════════════════════════

class TestF01AggregatedDuplicateReporting:
    def test_create_reports_all_colliding_fields_at_once(self, client, mock_admin_headers, override_auth):
        existing = valid_employee_payload()
        resp = client.post("/api/v1/hr/employees", headers=mock_admin_headers, json=existing)
        assert resp.status_code == 201, resp.text

        dup = valid_employee_payload(
            national_id=existing["national_id"],
            phone=existing["phone"],
            email=f"{_unique('other')}@test.com",
        )
        resp = client.post("/api/v1/hr/employees", headers=mock_admin_headers, json=dup)
        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        message = body["message"]
        assert "national_id" in message, f"national_id collision missing from: {message}"
        assert "phone" in message, f"phone collision missing from: {message}"

    def test_update_reports_all_colliding_fields_at_once(self, client, mock_admin_headers, override_auth):
        first = valid_employee_payload()
        second = valid_employee_payload()
        assert client.post("/api/v1/hr/employees", headers=mock_admin_headers, json=first).status_code == 201
        created = client.post("/api/v1/hr/employees", headers=mock_admin_headers, json=second)
        assert created.status_code == 201
        target_id = created.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/hr/employees/{target_id}",
            headers=mock_admin_headers,
            json={"national_id": first["national_id"], "phone": first["phone"]},
        )
        assert resp.status_code == 409
        message = resp.json()["message"]
        assert "national_id" in message
        assert "phone" in message


# ═══════════════════════════════════════════════════════════════════════════════
# F-04 — Concurrent duplicate insert yields typed conflict, never HTTP 500
# ═══════════════════════════════════════════════════════════════════════════════

def _raise_unique_violation(*args, **kwargs):
    raise IntegrityError(
        statement="INSERT INTO employees (...) VALUES (...)",
        params=None,
        orig=Exception(
            'duplicate key value violates unique constraint "uq_employees_phone"'
        ),
    )


class TestF04RaceSafeConflictTranslation:
    def test_concurrent_create_insert_maps_to_conflict_error(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        from app.modules.hr.repositories.employee_repository import EmployeeRepository

        monkeypatch.setattr(EmployeeRepository, "create", _raise_unique_violation)
        resp = client.post(
            "/api/v1/hr/employees", headers=mock_admin_headers, json=valid_employee_payload()
        )
        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["success"] is False
        assert body["error"] == "ConflictError"
        assert "phone" in body["message"]

    def test_concurrent_update_write_maps_to_conflict_error(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        from app.modules.hr.repositories.employee_repository import EmployeeRepository

        created = _create_employee(client, mock_admin_headers)
        monkeypatch.setattr(EmployeeRepository, "update", _raise_unique_violation)

        resp = client.put(
            f"/api/v1/hr/employees/{created['id']}",
            headers=mock_admin_headers,
            json={"phone": f"011{str(uuid.uuid4().int)[:8]}"},
        )
        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["error"] == "ConflictError"
        assert "phone" in body["message"]


# ═══════════════════════════════════════════════════════════════════════════════
# F-05 — Partial employment updates never violate the contract CHECK constraint
# ═══════════════════════════════════════════════════════════════════════════════

class TestF05UpdateEmploymentNormalization:
    def test_setting_percentage_alone_on_non_contract_employee_succeeds(
        self, client, mock_admin_headers, override_auth
    ):
        created = _create_employee(client, mock_admin_headers, employment_type="full_time")

        resp = client.put(
            f"/api/v1/hr/employees/{created['id']}",
            headers=mock_admin_headers,
            json={"contract_percentage": 50},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["employment_type"] == "full_time"
        assert body["data"]["contract_percentage"] is None

    def test_switching_to_contract_without_percentage_applies_default(
        self, client, mock_admin_headers, override_auth
    ):
        created = _create_employee(
            client, mock_admin_headers, employment_type="full_time", monthly_salary=9000.0
        )

        resp = client.put(
            f"/api/v1/hr/employees/{created['id']}",
            headers=mock_admin_headers,
            json={"employment_type": "contract"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["employment_type"] == "contract"
        assert body["data"]["contract_percentage"] is not None


# ═══════════════════════════════════════════════════════════════════════════════
# F-08 — Credentials rejected together BEFORE any remote provisioning call
# ═══════════════════════════════════════════════════════════════════════════════

class TestF08CredentialPreValidation:
    def test_invalid_email_and_short_password_rejected_without_remote_call(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        from app.modules.hr.services.staff_account_service import StaffAccountService

        created = _create_employee(client, mock_admin_headers)

        def _must_not_run(self, dto):
            raise AssertionError("create_account must not execute for invalid credentials")

        monkeypatch.setattr(StaffAccountService, "create_account", _must_not_run)

        resp = _provision(
            client, mock_admin_headers, created["id"],
            email="not-an-email", password="short",
        )
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["success"] is False
        message = str(body["message"])
        assert "email" in message.lower()
        assert "password" in message.lower()

    def test_password_below_service_minimum_rejected_pre_remote(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        from app.modules.hr.services.staff_account_service import StaffAccountService

        created = _create_employee(client, mock_admin_headers)

        def _must_not_run(self, dto):
            raise AssertionError("remote call must not happen for short passwords")

        monkeypatch.setattr(StaffAccountService, "create_account", _must_not_run)

        resp = _provision(
            client, mock_admin_headers, created["id"], password="Ab1!Ab1!"
        )  # 8 chars: passes API floor, below enforced minimum
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert "password" in str(body["message"]).lower()


# ═══════════════════════════════════════════════════════════════════════════════
# F-02 — Remote failures classified honestly (conflict vs unavailable)
# ═══════════════════════════════════════════════════════════════════════════════

class _FakeRemoteUser:
    def __init__(self, uid):
        self.id = uid


def _install_fake_supabase(monkeypatch, admin_stub):
    """Replace the Supabase client handed to StaffAccountService."""
    from app.modules.hr.services import staff_account_service as svc_module

    fake_client = type("C", (), {"auth": type("A", (), {"admin": admin_stub})()})()
    original_init = svc_module.StaffAccountService.__init__

    def _init_with_fake(self, uow, supabase_client=None):
        original_init(self, uow, supabase_client)
        self._supabase = fake_client

    monkeypatch.setattr(svc_module.StaffAccountService, "__init__", _init_with_fake)


class TestF02RemoteFailureClassification:
    def test_email_taken_signal_returns_conflict_error(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        created = _create_employee(client, mock_admin_headers)

        class _FakeAdmin:
            @staticmethod
            def create_user(data):
                raise Exception("User already registered")

        _install_fake_supabase(monkeypatch, _FakeAdmin)

        resp = _provision(client, mock_admin_headers, created["id"])
        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["error"] == "ConflictError"
        assert "already" in body["message"].lower()

    def test_other_remote_failure_returns_clear_retry_message_not_conflict(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        created = _create_employee(client, mock_admin_headers)

        class _FakeAdmin:
            @staticmethod
            def create_user(data):
                raise ConnectionError("network unreachable")

        _install_fake_supabase(monkeypatch, _FakeAdmin)

        resp = _provision(client, mock_admin_headers, created["id"])
        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["error"] == "BusinessRuleError"
        assert "nothing was created" in body["message"].lower()
        assert "retry" in body["message"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# F-03 — Midway failure compensates: zero orphaned identities / partial rows
# ═══════════════════════════════════════════════════════════════════════════════

class TestF03ZeroPartialStateOnMidwayFailure:
    def test_local_failure_after_remote_creation_compensates_and_leaves_no_rows(
        self, client, mock_admin_headers, override_auth, db_session, monkeypatch
    ):
        from app.modules.auth.models.auth_models import User as UserModel
        from app.modules.hr.models.employee_models import Employee
        from app.modules.hr.repositories.staff_account_repository import (
            StaffAccountRepository,
        )

        created = _create_employee(client, mock_admin_headers)
        employee_id = created["id"]

        deleted_uids: list[str] = []

        class _FakeAdmin:
            @staticmethod
            def create_user(data):
                return type("R", (), {"user": _FakeRemoteUser("orphan-uid-123")})()

            @staticmethod
            def delete_user(uid):
                deleted_uids.append(uid)

        _install_fake_supabase(monkeypatch, _FakeAdmin)

        def _boom(self, employee, dto, supabase_uid):
            raise RuntimeError("simulated local-side failure")

        monkeypatch.setattr(StaffAccountRepository, "create_linked_account", _boom)

        email = f"{_unique('comp')}@test.com"
        resp = _provision(client, mock_admin_headers, employee_id, email=email)

        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["error"] == "BusinessRuleError"
        assert "nothing was created" in body["message"].lower()
        assert deleted_uids == ["orphan-uid-123"], "remote identity must be compensated"

        leaked = db_session.exec(
            select(UserModel).where(UserModel.username == email)
        ).first()
        assert leaked is None, "no partial local user row may persist"

        emp_row = db_session.get(Employee, employee_id)
        assert emp_row.user_id is None, "employee must remain unlinked"


# ═══════════════════════════════════════════════════════════════════════════════
# F-06 — Staff accounts overview carries complete data (no null placeholders)
# F-07 — Deactivating a linked employee blocks their account automatically
# ═══════════════════════════════════════════════════════════════════════════════

class TestF06CompleteStaffAccountListing:
    def test_listing_includes_real_email_job_title_and_created_at(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        job_title = _unique("Lead Engineer")
        created = _create_employee(client, mock_admin_headers, job_title=job_title)
        email = f"{_unique('full')}@test.com"

        class _FakeAdmin:
            @staticmethod
            def create_user(data):
                return type("R", (), {"user": _FakeRemoteUser(f"uid-{_unique('x')}")})()

            @staticmethod
            def delete_user(uid):
                pass

        _install_fake_supabase(monkeypatch, _FakeAdmin)

        resp = _provision(client, mock_admin_headers, created["id"], email=email)
        assert resp.status_code == 201, resp.text

        listing = client.get("/api/v1/hr/staff-accounts", headers=mock_admin_headers)
        assert listing.status_code == 200, listing.text
        accounts = listing.json()["data"]
        match = [a for a in accounts if a["employee_id"] == created["id"]]
        assert match, "provisioned account missing from overview"
        acc = match[0]
        assert acc["email"] == email
        assert acc["job_title"] == job_title
        assert acc["created_at"] is not None


class TestF07DeactivationBlocksLinkedAccount:
    def test_deactivating_employee_blocks_their_account(
        self, client, mock_admin_headers, override_auth, monkeypatch
    ):
        created = _create_employee(client, mock_admin_headers)

        class _FakeAdmin:
            @staticmethod
            def create_user(data):
                return type("R", (), {"user": _FakeRemoteUser(f"uid-{_unique('y')}")})()

            @staticmethod
            def delete_user(uid):
                pass

        _install_fake_supabase(monkeypatch, _FakeAdmin)

        resp = _provision(client, mock_admin_headers, created["id"])
        assert resp.status_code == 201, resp.text

        deact = client.put(
            f"/api/v1/hr/employees/{created['id']}",
            headers=mock_admin_headers,
            json={"is_active": False},
        )
        assert deact.status_code == 200, deact.text

        listing = client.get("/api/v1/hr/staff-accounts", headers=mock_admin_headers)
        accounts = listing.json()["data"]
        match = [a for a in accounts if a["employee_id"] == created["id"]]
        assert match and match[0]["is_active"] is False, (
            "linked account must be blocked when employee is deactivated"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# F-08 — Second provisioning for an already-linked employee is refused
# ═══════════════════════════════════════════════════════════════════════════════

class TestFR008SecondAccountRefusal:
    def test_refused_before_any_remote_call(
        self, client, mock_admin_headers, override_auth, db_session, monkeypatch
    ):
        from app.modules.auth.models.auth_models import User as UserModel

        emp = create_test_employee(db_session)
        user = UserModel(
            username=f"{_unique('linked')}@test.com",
            role="admin",
            supabase_uid=_unique("sb-uid"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        emp.user_id = user.id
        db_session.add(emp)
        db_session.commit()

        class _ExplodingAdmin:
            @staticmethod
            def create_user(data):
                raise AssertionError("remote create_user must not be reached")

            @staticmethod
            def delete_user(uid):
                raise AssertionError("compensation must not be needed")

        _install_fake_supabase(monkeypatch, _ExplodingAdmin)

        attempted_email = f"{_unique('dup')}@test.com"
        resp = _provision(client, mock_admin_headers, emp.id, email=attempted_email)
        assert resp.status_code == 409, resp.text
        assert "already has an account" in resp.json()["message"]

        leftovers = db_session.exec(
            select(UserModel).where(UserModel.username == attempted_email)
        ).all()
        assert leftovers == [], "no local identity may be created for a refused request"
