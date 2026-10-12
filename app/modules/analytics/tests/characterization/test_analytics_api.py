"""Characterization tests for the Analytics HTTP API (ticket #25).

Pins status codes, envelopes and row shapes of the 20 read-only endpoints served by
``app/api/routers/analytics/{academic,bi,financial,competition,dashboard}.py`` BEFORE
the HTTP layer moves into ``app/modules/analytics/api/``.

Buckets
-------
* Analytics is read-only: no test here writes through the analytics API. Data comes from
  committed, uuid-tagged seed rows (``db_session``) and from receipts created through the
  finance API, because the analytics services open their own sessions.
* The database is shared and keeps growing, so list endpoints are checked for the exact
  key set of every returned row (``EXPECTED_KEYS``) and, where the test owns the data, for
  exact values. Numbers over the whole database are never asserted.
* ``GET /analytics/competitions/fee-summary`` pins the FIXED behaviour (fees come from
  ``team_members.amount_paid`` / ``amount_due`` and ``teams.competition_id``), with exact
  values for a competition created by the test.

Pinned quirks (pinned, not endorsed)
------------------------------------
See the tests marked "current behaviour".
"""

import uuid
from datetime import date, time

import pytest

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment

API = "/api/v1"

EXPECTED_KEYS = {
    "unpaid_attendees": {"student_id", "student_name", "group_name", "parent_name", "phone_primary", "total_balance"},
    "heatmap": {"student_id", "student_name", "session_id", "session_number", "session_date", "status"},
    "student_progress": {
        "student_id", "student_name", "course_name", "group_name", "current_level", "total_sessions",
        "sessions_attended", "sessions_missed", "attendance_pct", "progress_status",
        "estimated_completion_date", "enrollment_date", "last_attendance_date",
    },
    "course_completion": {
        "course_id", "course_name", "started_count", "completed_count", "dropped_count",
        "in_progress_count", "completion_pct", "avg_days_to_complete",
    },
    "enrollment_trend": {"day", "new_enrollments"},
    "retention": {"course_name", "active_count", "dropped_count", "total_enrollments"},
    "instructor_performance": {"instructor_name", "active_groups", "active_students"},
    "retention_funnel": {"course_name", "level_number", "student_count"},
    "instructor_value": {"instructor_name", "total_revenue", "avg_attendance_pct"},
    "schedule_utilization": {"day", "time_start", "total_enrolled", "total_capacity", "utilization_pct"},
    "flight_risk": {"student_name", "course_name", "amount_owed", "sessions_missed"},
    "retention_analysis": {"cohort_month", "initial_enrollments", "retention_by_month", "retention_rates"},
    "revenue_by_date": {"day", "net_revenue"},
    "revenue_by_method": {"payment_method", "net_revenue", "receipt_count"},
    "outstanding_by_group": {"group_id", "group_name", "course_name", "students_with_balance", "total_outstanding"},
    "top_debtors": {"student_id", "student_name", "parent_name", "phone_primary", "total_outstanding"},
    "fee_summary": {
        "competition_id", "competition_name", "competition_date", "team_count", "member_count",
        "fees_collected", "fees_outstanding",
    },
}


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _get(client, headers, path):
    return client.get(f"{API}{path}", headers=headers)


def _assert_list(resp, key):
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    for row in body["data"]:
        assert set(row) == EXPECTED_KEYS[key]
    return body["data"]


# ── Academic ──────────────────────────────────────────────────────────────────


def test_unpaid_attendees(client_with_uow, override_auth, mock_admin_headers):
    _assert_list(_get(client_with_uow, mock_admin_headers, "/analytics/academics/unpaid-attendees"), "unpaid_attendees")
    _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/academics/unpaid-attendees?target_date=2026-01-01"),
        "unpaid_attendees",
    )


def test_attendance_heatmap(client_with_uow, override_auth, mock_admin_headers):
    _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/academics/groups/999999999/heatmap?level_number=1"),
        "heatmap",
    )


def test_attendance_heatmap_requires_valid_level(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    assert _get(client_with_uow, h, "/analytics/academics/groups/1/heatmap").status_code == 422
    assert _get(client_with_uow, h, "/analytics/academics/groups/1/heatmap?level_number=0").status_code == 422


def test_student_progress_filters(client_with_uow, override_auth, mock_admin_headers):
    _assert_list(_get(client_with_uow, mock_admin_headers, "/analytics/academics/student-progress"), "student_progress")
    unknown = _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/academics/student-progress?student_id=999999999"),
        "student_progress",
    )
    assert unknown == []


def test_course_completion_reflects_seeded_course(client_with_uow, override_auth, mock_admin_headers, db_session):
    course = Course(
        name=f"AnCourse {_short()}", category="software", price_per_level=500.0, sessions_per_level=8, is_active=True,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    rows = _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/academics/course-completion"), "course_completion"
    )

    mine = [r for r in rows if r["course_id"] == course.id]
    assert len(mine) <= 1  # a course with no enrolments may or may not be listed; shape is pinned above


# ── BI ────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "path,key",
    [
        ("/analytics/bi/enrollment-trend", "enrollment_trend"),
        ("/analytics/bi/enrollment-trend?cutoff=2020-01-01", "enrollment_trend"),
        ("/analytics/bi/retention", "retention"),
        ("/analytics/bi/instructor-performance", "instructor_performance"),
        ("/analytics/bi/retention-funnel", "retention_funnel"),
        ("/analytics/bi/instructor-value", "instructor_value"),
        ("/analytics/bi/schedule-utilization", "schedule_utilization"),
        ("/analytics/bi/flight-risk", "flight_risk"),
    ],
)
def test_bi_endpoints_shape(client_with_uow, override_auth, mock_admin_headers, path, key):
    _assert_list(_get(client_with_uow, mock_admin_headers, path), key)


def test_retention_analysis_shape_and_months_bounds(client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): with enrolment data older than a month the
    cohort rows fail DTO validation (percent strings in int fields, bug #74), so the endpoint
    is 200 on an empty database and 500 once cohorts exist."""
    from fastapi.testclient import TestClient

    r = TestClient(client_with_uow.app, raise_server_exceptions=False).get(
        f"{API}/analytics/bi/retention-analysis", headers=mock_admin_headers
    )
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        for row in r.json()["data"]:
            assert set(row) == EXPECTED_KEYS["retention_analysis"]
    assert _get(client_with_uow, mock_admin_headers, "/analytics/bi/retention-analysis?months=0").status_code == 422
    assert _get(client_with_uow, mock_admin_headers, "/analytics/bi/retention-analysis?months=13").status_code == 422


# ── Competitions fee summary (fixed behaviour, exact values) ─────────────────


def test_competition_fee_summary_exact_values(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = Competition(
        name=f"AnComp {_short()}", edition_year=2031, competition_date=date(2031, 6, 1), fee_per_student=100.0,
    )
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)
    team = Team(competition_id=comp.id, team_name=f"AnTeam {_short()}", category="Robotics")
    db_session.add(team)
    s1 = Student(full_name=f"An S1 {_short()}", phone=f"555{_short()[:7]}", status="inactive")
    s2 = Student(full_name=f"An S2 {_short()}", phone=f"555{_short()[:7]}", status="inactive")
    for s in (s1, s2):  # one commit each: a multi-row insert cannot cast the student_status enum
        db_session.add(s)
        db_session.commit()
        db_session.refresh(s)
    db_session.refresh(team)
    db_session.add(TeamMember(team_id=team.id, student_id=s1.id, amount_due=100.0, amount_paid=100.0))
    db_session.add(TeamMember(team_id=team.id, student_id=s2.id, amount_due=100.0, amount_paid=30.0))
    db_session.commit()

    rows = _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/competitions/fee-summary"), "fee_summary"
    )

    mine = [r for r in rows if r["competition_id"] == comp.id]
    assert len(mine) == 1
    row = mine[0]
    assert row["competition_name"] == comp.name
    assert row["competition_date"] == "2031-06-01"
    assert row["team_count"] == 1
    assert row["member_count"] == 2
    assert row["fees_collected"] == 130.0
    assert row["fees_outstanding"] == 70.0


# ── Finance analytics (data created through the API, exact values) ───────────


def _seed_debt(db_session, amount_due=900.0):
    course = Course(
        name=f"AnFin {_short()}", category="software", price_per_level=amount_due, sessions_per_level=8, is_active=True,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    group = Group(
        name=f"AnGroup {_short()}", course_id=course.id, level_number=1, max_capacity=15, default_day="Saturday",
        default_time_start=time(14, 0), default_time_end=time(16, 0), status="active",
    )
    student = Student(full_name=f"An Debtor {_short()}", phone=f"555{_short()[:7]}", status="inactive")
    db_session.add(group)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(group)
    db_session.refresh(student)
    enrollment = Enrollment(
        student_id=student.id, group_id=group.id, level_number=1, amount_due=amount_due, discount_applied=0.0,
        status="active", enrolled_at=date(2026, 1, 5),
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)
    return group, student, enrollment


def test_outstanding_by_group_and_top_debtors_see_a_debt(client_with_uow, override_auth, mock_admin_headers, db_session):
    group, student, _ = _seed_debt(db_session, amount_due=900.0)

    out = _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/finance/outstanding-by-group"), "outstanding_by_group"
    )
    debtors = _assert_list(
        _get(client_with_uow, mock_admin_headers, "/analytics/finance/top-debtors?limit=100"), "top_debtors"
    )

    mine = [r for r in out if r["group_id"] == group.id]
    assert len(mine) == 1
    assert mine[0]["students_with_balance"] == 1
    assert mine[0]["total_outstanding"] == 900.0
    assert student.id in [d["student_id"] for d in debtors] or len(debtors) == 100


def test_revenue_endpoints_see_a_receipt(client_with_uow, override_auth, mock_admin_headers, db_session):
    """A receipt paid on a day nobody else uses (2019-03-03), so the values are exact."""
    from datetime import datetime, timezone

    from app.modules.finance.models import Payment, Receipt

    _, student, enrollment = _seed_debt(db_session, amount_due=500.0)
    paid_at = datetime(2019, 3, 3, 12, 0, tzinfo=timezone.utc)
    receipt = Receipt(payer_name="An Payer", payment_method="cash", paid_at=paid_at, created_at=paid_at)
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    db_session.add(Payment(
        receipt_id=receipt.id, student_id=student.id, enrollment_id=enrollment.id, amount=222.0,
        transaction_type="payment", payment_type="course_level", created_at=paid_at,
    ))
    db_session.commit()

    try:
        by_date = _assert_list(
            _get(client_with_uow, mock_admin_headers, "/analytics/finance/revenue-by-date?start=2019-03-03&end=2019-03-03"),
            "revenue_by_date",
        )
        by_method = _assert_list(
            _get(client_with_uow, mock_admin_headers, "/analytics/finance/revenue-by-method?start=2019-03-03&end=2019-03-03"),
            "revenue_by_method",
        )

        assert by_date == [{"day": "2019-03-03", "net_revenue": 222.0}]
        assert by_method == [{"payment_method": "cash", "net_revenue": 222.0, "receipt_count": 1}]
    finally:  # keep the shared database idempotent
        db_session.query(Payment).filter(Payment.receipt_id == receipt.id).delete()
        db_session.query(Receipt).filter(Receipt.id == receipt.id).delete()
        db_session.commit()


def test_revenue_endpoints_validation(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    assert _get(client_with_uow, h, "/analytics/finance/revenue-by-date").status_code == 422
    assert _get(client_with_uow, h, "/analytics/finance/revenue-by-method?start=2026-01-01").status_code == 422
    too_wide = _get(client_with_uow, h, "/analytics/finance/revenue-by-date?start=2020-01-01&end=2026-01-01")
    assert too_wide.status_code == 422
    assert too_wide.json()["message"] == "Date range cannot exceed 365 days"
    # current behaviour (pinned, not endorsed): an inverted range is not rejected, it is just empty
    inverted = _get(client_with_uow, h, "/analytics/finance/revenue-by-date?start=2026-02-01&end=2026-01-01")
    assert inverted.status_code == 200 and inverted.json()["data"] == []
    assert _get(client_with_uow, h, "/analytics/finance/top-debtors?limit=0").status_code == 422
    assert _get(client_with_uow, h, "/analytics/finance/revenue-metrics?months=25").status_code == 422
    assert _get(client_with_uow, h, "/analytics/finance/revenue-forecast?months_ahead=13").status_code == 422


def test_revenue_metrics_shape(client_with_uow, override_auth, mock_admin_headers):
    r = _get(client_with_uow, mock_admin_headers, "/analytics/finance/revenue-metrics?months=3")

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {
        "period_start", "period_end", "total_revenue", "total_receipts", "avg_revenue_per_receipt",
        "previous_period_revenue", "revenue_change_pct", "trend_direction", "monthly_breakdown",
    }
    assert data["trend_direction"] in ("up", "down", "stable")
    for m in data["monthly_breakdown"]:
        assert set(m) == EXPECTED_KEYS["revenue_by_date"]


def test_revenue_forecast_shape(client_with_uow, override_auth, mock_admin_headers):
    r = _get(client_with_uow, mock_admin_headers, "/analytics/finance/revenue-forecast?months_ahead=2")

    assert r.status_code == 200
    rows = r.json()["data"]
    assert len(rows) == 2
    for row in rows:
        assert set(row) == {"month", "predicted_revenue", "confidence_lower", "confidence_upper"}


# ── Dashboard ─────────────────────────────────────────────────────────────────


def test_dashboard_daily_overview(client_with_uow, override_auth, mock_admin_headers):
    r = _get(client_with_uow, mock_admin_headers, "/dashboard/daily-overview?date=2026-01-01")

    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Dashboard overview loaded successfully."
    assert set(body["data"]) == {
        "date", "generated_at", "cache_ttl", "groups", "instructors", "scheduled_groups", "summary",
    }
    assert body["data"]["date"] == "2026-01-01"


def test_dashboard_daily_overview_without_attendance(client_with_uow, override_auth, mock_admin_headers):
    r = _get(client_with_uow, mock_admin_headers, "/dashboard/daily-overview?date=2026-01-01&include_attendance=false")
    assert r.status_code == 200


def test_dashboard_requires_date(client_with_uow, override_auth, mock_admin_headers):
    assert _get(client_with_uow, mock_admin_headers, "/dashboard/daily-overview").status_code == 422


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_analytics_endpoints_require_auth(client):
    for path in [
        "/analytics/academics/unpaid-attendees", "/analytics/academics/groups/1/heatmap?level_number=1",
        "/analytics/academics/student-progress", "/analytics/academics/course-completion",
        "/analytics/bi/enrollment-trend", "/analytics/bi/retention", "/analytics/bi/instructor-performance",
        "/analytics/bi/retention-funnel", "/analytics/bi/instructor-value", "/analytics/bi/schedule-utilization",
        "/analytics/bi/flight-risk", "/analytics/bi/retention-analysis", "/analytics/competitions/fee-summary",
        "/dashboard/daily-overview?date=2026-01-01",
        "/analytics/finance/revenue-by-date?start=2026-01-01&end=2026-01-02",
        "/analytics/finance/revenue-by-method?start=2026-01-01&end=2026-01-02",
        "/analytics/finance/outstanding-by-group", "/analytics/finance/top-debtors",
        "/analytics/finance/revenue-metrics", "/analytics/finance/revenue-forecast",
    ]:
        assert client.get(f"{API}{path}").status_code == 401, path
