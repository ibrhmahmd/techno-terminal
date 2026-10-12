"""Audit API (#114): the integrity checks A–I, admin-only and read-only."""

from datetime import date

import pytest

from app.modules.audit.constants import SCENARIOS
from app.modules.finance.tests.characterization.test_finance_api import _seed_enrollment

API = "/api/v1/audit"


def _seed_zero_charge(session):
    """An active enrollment whose amount_due is 0 (check A). Courses can't be free, so the
    enrollment is created normally and its charge zeroed."""
    course, group, student, enrollment = _seed_enrollment(session)
    enrollment.amount_due = 0
    session.add(enrollment)
    session.commit()
    return course, group, student, enrollment


def _get(client, headers, path):
    return client.get(f"{API}{path}", headers=headers)


def test_scenarios_list_every_check_errors_first(client_with_uow, override_auth, mock_admin_headers):
    r = _get(client_with_uow, mock_admin_headers, "/scenarios")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    rows = body["data"]
    assert {row["code"] for row in rows} == {s["code"] for s in SCENARIOS}
    assert all(set(row) == {"code", "label", "severity", "anomaly_count"} for row in rows)
    order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    keys = [(order[row["severity"]], row["code"]) for row in rows]
    assert keys == sorted(keys)


def test_zero_charge_enrollment_shows_up_in_check_a(client_with_uow, override_auth, mock_admin_headers, uow):
    _, group, student, enrollment = _seed_zero_charge(uow.session)

    counts = {row["code"]: row["anomaly_count"] for row in _get(client_with_uow, mock_admin_headers, "/scenarios").json()["data"]}
    assert counts["A"] >= 1

    r = _get(client_with_uow, mock_admin_headers, "/scenarios/A?limit=500")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1 and body["skip"] == 0 and body["limit"] == 500
    mine = [row for row in body["data"] if row["enrollment_id"] == enrollment.id]
    assert len(mine) == 1
    assert mine[0]["student_name"] == student.full_name
    assert mine[0]["group_name"] == group.name
    assert mine[0]["enrolled_at"] == "2026-01-05"


def test_since_filter_and_lowercase_code(client_with_uow, override_auth, mock_admin_headers, uow):
    _, _, _, enrollment = _seed_zero_charge(uow.session)
    later = _get(client_with_uow, mock_admin_headers, "/scenarios/a?since=2026-01-06&limit=500").json()
    assert enrollment.id not in [row["enrollment_id"] for row in later["data"]]
    same_day = _get(client_with_uow, mock_admin_headers, "/scenarios/a?since=2026-01-05&limit=500").json()
    assert enrollment.id in [row["enrollment_id"] for row in same_day["data"]]


def test_pagination_total_is_independent_of_the_page(client_with_uow, override_auth, mock_admin_headers, uow):
    _seed_zero_charge(uow.session)
    _seed_zero_charge(uow.session)
    full = _get(client_with_uow, mock_admin_headers, "/scenarios/A?limit=500").json()
    page = _get(client_with_uow, mock_admin_headers, "/scenarios/A?skip=1&limit=1").json()
    assert page["total"] == full["total"] >= 2
    assert len(page["data"]) == 1
    assert page["data"][0] == full["data"][1]


@pytest.mark.parametrize("code", [s["code"] for s in SCENARIOS])
def test_every_check_returns_its_typed_rows(client_with_uow, override_auth, mock_admin_headers, code):
    r = _get(client_with_uow, mock_admin_headers, f"/scenarios/{code}")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


def test_unknown_check_is_404(client_with_uow, override_auth, mock_admin_headers):
    r = _get(client_with_uow, mock_admin_headers, "/scenarios/Z")
    assert r.status_code == 404
    assert r.json()["error"] == "NotFoundError"


@pytest.mark.parametrize("query", ["skip=-1", "limit=0", "limit=501", "since=not-a-date"])
def test_invalid_query_is_422(client_with_uow, override_auth, mock_admin_headers, query):
    assert _get(client_with_uow, mock_admin_headers, f"/scenarios/A?{query}").status_code == 422


@pytest.mark.parametrize("path", ["/scenarios", "/scenarios/A"])
def test_requires_auth(client, path):
    assert client.get(f"{API}{path}").status_code == 401
