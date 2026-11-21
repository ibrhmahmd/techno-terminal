"""#274: deactivating a login bans its Supabase user, reactivating unbans, failures never roll back."""
import uuid

from app.modules.auth.models.auth_models import User
from app.modules.hr.models.employee_models import Employee

ADMIN_USERS = "/api/v1/admin/users"


def _user(session, **kw) -> User:
    user = User(
        username=f"u_{uuid.uuid4().hex[:8]}@test.local",
        role="admin",
        supabase_uid=f"ban-{uuid.uuid4().hex}",
        is_active=kw.pop("is_active", True),
        **kw,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _calls(admin):
    return [c.args for c in admin.auth.admin.update_user_by_id.call_args_list]


def test_deactivate_bans_and_reactivate_unbans(
    client_with_uow, override_system_admin_auth, system_admin_headers, db_session, supabase_ban_admin
):
    user = _user(db_session)

    r = client_with_uow.patch(f"{ADMIN_USERS}/{user.id}", headers=system_admin_headers, json={"is_active": False})
    assert r.status_code == 200, r.text
    assert _calls(supabase_ban_admin) == [(user.supabase_uid, {"ban_duration": "876000h"})]

    supabase_ban_admin.reset_mock()
    r = client_with_uow.patch(f"{ADMIN_USERS}/{user.id}", headers=system_admin_headers, json={"is_active": True})
    assert r.status_code == 200, r.text
    assert _calls(supabase_ban_admin) == [(user.supabase_uid, {"ban_duration": "none"})]


def test_role_only_update_does_not_touch_supabase(
    client_with_uow, override_system_admin_auth, system_admin_headers, db_session, supabase_ban_admin
):
    user = _user(db_session)
    r = client_with_uow.patch(f"{ADMIN_USERS}/{user.id}", headers=system_admin_headers, json={"role": "admin"})
    assert r.status_code == 200, r.text
    assert _calls(supabase_ban_admin) == []


def test_supabase_failure_keeps_local_deactivation(
    client_with_uow, override_system_admin_auth, system_admin_headers, db_session, supabase_ban_admin
):
    user = _user(db_session)
    supabase_ban_admin.auth.admin.update_user_by_id.side_effect = RuntimeError("supabase down")

    r = client_with_uow.patch(f"{ADMIN_USERS}/{user.id}", headers=system_admin_headers, json={"is_active": False})

    assert r.status_code == 200, r.text
    assert r.json()["data"]["is_active"] is False


def test_employee_deactivate_and_delete_ban_linked_login(
    client_with_uow, override_auth, mock_admin_headers, db_session, supabase_ban_admin
):
    def employee_with_login():
        tag = uuid.uuid4().hex[:8]
        emp = Employee(
            full_name=f"Ban {tag}", phone=f"+2010{tag}", email=f"{tag}@t.test", national_id=f"N{tag}",
            university="U", major="M", job_title="Instructor", employment_type="full_time", monthly_salary=1.0, is_active=True,
        )
        db_session.add(emp)
        db_session.commit()
        return emp, _user(db_session, employee_id=emp.id)

    emp, user = employee_with_login()
    r = client_with_uow.put(
        f"/api/v1/hr/employees/{emp.id}", headers=mock_admin_headers, json={"is_active": False}
    )
    assert r.status_code == 200, r.text
    assert _calls(supabase_ban_admin) == [(user.supabase_uid, {"ban_duration": "876000h"})]

    supabase_ban_admin.reset_mock()
    emp, user = employee_with_login()
    r = client_with_uow.delete(f"/api/v1/hr/employees/{emp.id}", headers=mock_admin_headers)
    assert r.status_code == 200, r.text
    assert _calls(supabase_ban_admin) == [(user.supabase_uid, {"ban_duration": "876000h"})]
