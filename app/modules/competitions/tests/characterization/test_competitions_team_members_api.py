"""Characterization tests for the Teams HTTP API, members / fees / placement part (ticket #21).

Pins the member, fee and placement endpoints served by
``app/api/routers/competitions/teams_router.py`` BEFORE the HTTP layer moves into
``app/modules/competitions/api/``:

    GET/POST /teams/{id}/members, DELETE /teams/{id}/members/{student_id},
    POST .../pay, POST .../refund, PATCH /teams/{id}/placement

The fee endpoints (pay, refund) move to finance in ticket #34; they are pinned here
first, including the refund error path.

Buckets
-------
* ``TeamService`` opens its own ``get_session()`` and really commits; rows are
  seeded through the committed ``db_session`` (uuid-tagged). Notifications are
  replaced by a no-op.
* Placement is only allowed within 30 days after the competition date, so those
  tests build a competition dated a few days ago relative to ``date.today()``.

Pinned quirks (pinned, not endorsed)
------------------------------------
See the individual tests marked "current behaviour".
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models.student_models import Student


@pytest.fixture
def noop_notifications(app):
    """Replace every notifier port provider with a no-op so nothing can be dispatched."""
    from app.testing.noop_notifiers import noop_notifiers

    with noop_notifiers(app) as stub:
        yield stub


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_competition(db_session, **overrides) -> Competition:
    comp = Competition(
        name=overrides.pop("name", f"Comp {_short()}"),
        edition_year=overrides.pop("edition_year", 2026),
        competition_date=overrides.pop("competition_date", date(2026, 5, 1)),
        location=overrides.pop("location", "Cairo"),
        fee_per_student=overrides.pop("fee_per_student", 100.0),
        **overrides,
    )
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)
    return comp


def _make_team(db_session, competition_id: int, **overrides) -> Team:
    team = Team(
        competition_id=competition_id,
        team_name=overrides.pop("team_name", f"Team {_short()}"),
        category=overrides.pop("category", "Robotics"),
        subcategory=overrides.pop("subcategory", None),
        **overrides,
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


def _make_student(db_session, **overrides) -> Student:
    student = Student(
        full_name=overrides.pop("full_name", f"Student {_short()}"),
        phone=overrides.pop("phone", f"555{_short()[:7]}"),
        status=overrides.pop("status", "active"),
        **overrides,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def _add_member(db_session, team_id: int, student_id: int, **overrides) -> TeamMember:
    member = TeamMember(
        team_id=team_id,
        student_id=student_id,
        amount_due=overrides.pop("amount_due", 100.0),
        amount_paid=overrides.pop("amount_paid", 0.0),
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


def _setup(db_session, **comp_overrides):
    comp = _make_competition(db_session, **comp_overrides)
    team = _make_team(db_session, comp.id)
    student = _make_student(db_session)
    return comp, team, student


# ── GET /teams/{id}/members ───────────────────────────────────────────────────


def test_list_team_members(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id, amount_due=80.0)

    r = client_with_uow.get(f"/api/v1/teams/{team.id}/members", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"team_id", "team_name", "members"}
    assert data["team_id"] == team.id
    assert data["team_name"] == team.team_name
    m = data["members"][0]
    assert set(m) == {"team_member_id", "team_id", "team_name", "student_id", "student_name", "amount_due", "amount_paid"}
    assert m["student_id"] == student.id
    assert m["amount_due"] == 80.0


def test_list_team_members_empty_team_name_is_unknown(client_with_uow, override_auth, mock_admin_headers, db_session):
    """current behaviour (pinned, not endorsed): a team with no members reports team_name 'Unknown'."""
    _, team, _ = _setup(db_session)

    r = client_with_uow.get(f"/api/v1/teams/{team.id}/members", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == {"team_id": team.id, "team_name": "Unknown", "members": []}


# ── POST /teams/{id}/members ──────────────────────────────────────────────────


def test_add_team_member_crashes_with_500(app, client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    """current behaviour (pinned, not endorsed): every add-member of an existing team fails with
    500 because the service reads ``Student.is_active``, an attribute that does not exist
    (bug #56)."""
    _, team, student = _setup(db_session)

    r = TestClient(app, raise_server_exceptions=False).post(
        f"/api/v1/teams/{team.id}/members", headers=mock_admin_headers,
        json={"student_id": student.id, "amount_due": 60.0},
    )

    assert r.status_code == 500


def test_add_team_member_unknown_team(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    student = _make_student(db_session)
    r = client_with_uow.post(
        "/api/v1/teams/999999999/members", headers=mock_admin_headers, json={"student_id": student.id}
    )
    assert r.status_code == 404
    assert r.json()["message"] == "Team 999999999 not found."


# ── DELETE /teams/{id}/members/{student_id} ───────────────────────────────────


def test_remove_team_member(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id)

    r = client_with_uow.delete(f"/api/v1/teams/{team.id}/members/{student.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] is True
    assert r.json()["message"] == "Member removed successfully."


def test_remove_paid_team_member_is_blocked(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id, amount_paid=40.0)

    r = client_with_uow.delete(f"/api/v1/teams/{team.id}/members/{student.id}", headers=mock_admin_headers)

    assert r.status_code == 409
    assert r.json()["error"] == "BusinessRuleError"
    assert r.json()["message"] == "Cannot remove a team member who has already paid the competition fee."


def test_remove_missing_team_member_still_reports_success(client_with_uow, override_auth, mock_admin_headers, db_session):
    """current behaviour (pinned, not endorsed): removing a non-member is a 200 with data=False."""
    _, team, student = _setup(db_session)

    r = client_with_uow.delete(f"/api/v1/teams/{team.id}/members/{student.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] is False
    assert r.json()["message"] == "Member removed successfully."


# ── POST /teams/{id}/members/{student_id}/pay ─────────────────────────────────


def test_pay_competition_fee(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id, amount_due=100.0)

    r = client_with_uow.post(
        f"/api/v1/teams/{team.id}/members/{student.id}/pay", headers=mock_admin_headers,
        json={"amount": 40.0},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Payment processed successfully."
    assert set(body["data"]) == {"receipt_number", "payment_id", "amount", "amount_paid", "amount_due"}
    assert body["data"]["amount"] == 40.0
    assert body["data"]["amount_paid"] == 40.0
    assert body["data"]["amount_due"] == 100.0


def test_pay_competition_fee_validation(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post(
        "/api/v1/teams/1/members/1/pay", headers=mock_admin_headers, json={"amount": 0}
    )
    assert r.status_code == 422


def test_pay_competition_fee_unknown_member(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, team, student = _setup(db_session)

    r = client_with_uow.post(
        f"/api/v1/teams/{team.id}/members/{student.id}/pay", headers=mock_admin_headers, json={"amount": 10.0}
    )

    assert r.status_code == 404
    assert r.json()["message"] == f"Student {student.id} is not a member of team {team.id}."


# ── POST /teams/{id}/members/{student_id}/refund ──────────────────────────────


def test_refund_competition_fee_crashes_with_500(app, client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    """current behaviour (pinned, not endorsed): the refund fails with 500 after issuing the
    refund receipt, because ``RefundService._unlink_competition_payment`` selects with
    ``sqlalchemy.select`` and then reads ``payment.team_member_id`` on a Row (KeyError). The
    whole transaction rolls back, so no refund is ever recorded."""
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id, amount_due=100.0)
    client_with_uow.post(
        f"/api/v1/teams/{team.id}/members/{student.id}/pay", headers=mock_admin_headers, json={"amount": 50.0}
    )

    r = TestClient(app, raise_server_exceptions=False).post(
        f"/api/v1/teams/{team.id}/members/{student.id}/refund", headers=mock_admin_headers, json={"amount": 20.0}
    )

    assert r.status_code == 500


def test_refund_unknown_member_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, team, student = _setup(db_session)

    r = client_with_uow.post(
        f"/api/v1/teams/{team.id}/members/{student.id}/refund", headers=mock_admin_headers, json={"amount": 5.0}
    )

    assert r.status_code == 404
    assert r.json()["message"] == "Team member not found."


def test_refund_more_than_paid_is_400(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id, amount_paid=10.0)

    r = client_with_uow.post(
        f"/api/v1/teams/{team.id}/members/{student.id}/refund", headers=mock_admin_headers, json={"amount": 25.0}
    )

    assert r.status_code == 400
    assert r.json()["message"] == "Refund amount (25.0) exceeds amount paid (10.0)."


def test_refund_without_a_competition_payment(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    """Error path: paid amount recorded on the member but no refundable competition payment row."""
    _, team, student = _setup(db_session)
    _add_member(db_session, team.id, student.id, amount_due=100.0, amount_paid=30.0)

    r = client_with_uow.post(
        f"/api/v1/teams/{team.id}/members/{student.id}/refund", headers=mock_admin_headers, json={"amount": 10.0}
    )

    assert r.status_code == 409
    assert "No competition payment with enough refundable balance" in r.json()["message"]


# ── PATCH /teams/{id}/placement ───────────────────────────────────────────────


def test_update_placement(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    comp = _make_competition(db_session, competition_date=date.today() - timedelta(days=3))
    team = _make_team(db_session, comp.id)
    _add_member(db_session, team.id, _make_student(db_session).id)

    r = client_with_uow.patch(
        f"/api/v1/teams/{team.id}/placement", headers=mock_admin_headers,
        json={"placement_rank": 1, "placement_label": "Gold"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Placement updated successfully."
    assert body["data"]["placement_rank"] == 1
    assert body["data"]["placement_label"] == "Gold"


def test_update_placement_before_competition_date_is_409(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    comp = _make_competition(db_session, competition_date=date.today() + timedelta(days=10))
    team = _make_team(db_session, comp.id)

    r = client_with_uow.patch(
        f"/api/v1/teams/{team.id}/placement", headers=mock_admin_headers, json={"placement_rank": 1}
    )

    assert r.status_code == 409
    assert r.json()["message"] == "Cannot set placement before competition date."


def test_update_placement_window_closed_is_409(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    comp = _make_competition(db_session, competition_date=date.today() - timedelta(days=60))
    team = _make_team(db_session, comp.id)

    r = client_with_uow.patch(
        f"/api/v1/teams/{team.id}/placement", headers=mock_admin_headers, json={"placement_rank": 1}
    )

    assert r.status_code == 409
    assert r.json()["message"].startswith("Placement recording window closed.")


def test_update_placement_validation_and_not_found(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    assert client_with_uow.patch(
        "/api/v1/teams/1/placement", headers=mock_admin_headers, json={"placement_rank": 0}
    ).status_code == 422
    r = client_with_uow.patch(
        "/api/v1/teams/999999999/placement", headers=mock_admin_headers, json={"placement_rank": 1}
    )
    assert r.status_code == 404
    assert r.json()["message"] == "Team 999999999 not found."


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_team_member_endpoints_require_auth(client):
    assert client.get("/api/v1/teams/1/members").status_code == 401
    assert client.post("/api/v1/teams/1/members", json={"student_id": 1}).status_code == 401
    assert client.delete("/api/v1/teams/1/members/1").status_code == 401
    assert client.post("/api/v1/teams/1/members/1/pay", json={"amount": 1}).status_code == 401
    assert client.post("/api/v1/teams/1/members/1/refund", json={"amount": 1}).status_code == 401
    assert client.patch("/api/v1/teams/1/placement", json={"placement_rank": 1}).status_code == 401
