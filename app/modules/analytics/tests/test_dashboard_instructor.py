"""Instructor view of GET /dashboard/daily-overview (#220): own groups only, no money."""

import pytest

from app.api.deps import get_current_user
from app.modules.auth import User
from app.testing.db_helpers import (
    create_minimal_group_bundle,
    create_student_with_enrollment,
    create_test_employee,
)

URL = "/api/v1/dashboard/daily-overview?date="


@pytest.fixture
def seeded(uow):
    """Two instructors, one group each with a session on the same date and one unpaid student."""
    s = uow.session
    emp_a, emp_b = create_test_employee(s), create_test_employee(s)
    _, group_a, _, sessions_a = create_minimal_group_bundle(s, instructor_id=emp_a.id, session_count=1)
    _, group_b, _, sessions_b = create_minimal_group_bundle(s, instructor_id=emp_b.id, session_count=1)
    # Move B's session onto A's date so one date covers both groups.
    sessions_b[0].session_date = sessions_a[0].session_date
    s.add(sessions_b[0])
    s.commit()
    create_student_with_enrollment(s, group_a.id, amount_due=500)
    create_student_with_enrollment(s, group_b.id, amount_due=300)
    return {
        "date": sessions_a[0].session_date.isoformat(),
        "emp_a": emp_a, "emp_b": emp_b, "group_a": group_a, "group_b": group_b,
    }


def _call(app, client, role, employee_id, date):
    user = User(username=f"u_{role}", role=role, supabase_uid=f"x-{role}", is_active=True, employee_id=employee_id)

    async def _me():
        return user

    app.dependency_overrides[get_current_user] = _me
    try:
        return client.get(URL + date)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_instructor_sees_only_own_groups_without_money(app, client_with_uow, seeded):
    r = _call(app, client_with_uow, "instructor", seeded["emp_a"].id, seeded["date"])

    assert r.status_code == 200
    data = r.json()["data"]
    assert [g["group_id"] for g in data["scheduled_groups"]] == [seeded["group_a"].id]
    assert list(data["groups"]) == [str(seeded["group_a"].id)]
    assert data["summary"]["total_groups_today"] == 1
    assert data["summary"]["unique_instructor_ids"] == [seeded["emp_a"].id]
    roster = data["scheduled_groups"][0]["roster"]
    assert len(roster) == 1
    assert all(row["balance"] == -1 and row["billing_status"] is None for row in roster)


def test_instructor_without_employee_id_gets_empty_overview(app, client_with_uow, seeded):
    r = _call(app, client_with_uow, "instructor", None, seeded["date"])

    assert r.status_code == 200
    data = r.json()["data"]
    assert data["scheduled_groups"] == [] and data["groups"] == {}
    assert data["summary"]["total_groups_today"] == 0


def test_admin_sees_all_groups_with_real_balances(app, client_with_uow, seeded):
    r = _call(app, client_with_uow, "admin", None, seeded["date"])

    assert r.status_code == 200
    by_group = {g["group_id"]: g for g in r.json()["data"]["scheduled_groups"]}
    assert {seeded["group_a"].id, seeded["group_b"].id} <= set(by_group)
    row = by_group[seeded["group_a"].id]["roster"][0]
    assert row["balance"] == 500 and row["billing_status"] == "due"
