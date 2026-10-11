"""Characterization tests for the Teams HTTP API, team lifecycle part (ticket #21).

Pins status codes, envelopes and shapes of the endpoints served by
``app/api/routers/competitions/teams_router.py`` BEFORE the HTTP layer moves into
``app/modules/competitions/api/``:

    GET/POST /teams, GET/PUT/PATCH/DELETE /teams/{id}, GET /students/{id}/competitions

(Members, fees and placement are pinned in ``test_competitions_team_members_api.py``.)

Buckets
-------
* ``TeamService`` opens its own ``get_session()`` and really commits, so rows are
  seeded through the committed ``db_session`` with uuid-tagged names.
* Writes may schedule notifications, so the notification service is replaced by a
  no-op (``noop_notifications``).

Pinned quirks (pinned, not endorsed)
------------------------------------
* GET /teams without ``competition_id`` is a 400.
* PUT and PATCH /teams/{id} are the same handler; an empty body is a 400.
"""

import uuid
from datetime import date

import pytest

from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models.student_models import Student


@pytest.fixture
def noop_notifications(app):
    """Replace every notifier port provider with a no-op so nothing can be dispatched."""
    from tests.utils.noop_notifiers import noop_notifiers

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


_TEAM_FIELDS = {
    "id", "competition_id", "category", "subcategory", "group_id", "team_name",
    "coach_id", "project_name", "project_description", "placement_rank",
    "placement_label", "notes", "created_at",
}


# ── GET /teams ────────────────────────────────────────────────────────────────


def test_list_teams_with_members(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)
    student = _make_student(db_session)
    _add_member(db_session, team.id, student.id)

    r = client_with_uow.get(f"/api/v1/teams?competition_id={comp.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 1
    assert set(data[0]) == {"team", "members"}
    assert set(data[0]["team"]) == _TEAM_FIELDS
    assert data[0]["team"]["id"] == team.id
    assert [m["student_id"] for m in data[0]["members"]] == [student.id]
    assert set(data[0]["members"][0]) == {"id", "team_id", "student_id", "amount_due", "amount_paid"}


def test_list_teams_without_members(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)
    _add_member(db_session, team.id, _make_student(db_session).id)

    r = client_with_uow.get(
        f"/api/v1/teams?competition_id={comp.id}&include_members=false", headers=mock_admin_headers
    )

    assert r.status_code == 200
    assert r.json()["data"][0]["members"] == []


def test_list_teams_filters_by_category(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    _make_team(db_session, comp.id, category="Robotics")
    ai = _make_team(db_session, comp.id, category="AI")

    r = client_with_uow.get(
        f"/api/v1/teams?competition_id={comp.id}&category=AI", headers=mock_admin_headers
    )

    assert [t["team"]["id"] for t in r.json()["data"]] == [ai.id]


def test_list_teams_requires_competition_id(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/teams", headers=mock_admin_headers)

    assert r.status_code == 400
    assert r.json()["message"] == "competition_id is required"


# ── POST /teams ───────────────────────────────────────────────────────────────


def test_register_team(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    comp = _make_competition(db_session, fee_per_student=120.0)
    s1 = _make_student(db_session)
    s2 = _make_student(db_session)
    name = f"Reg {_short()}"

    r = client_with_uow.post(
        "/api/v1/teams", headers=mock_admin_headers,
        json={"competition_id": comp.id, "team_name": name, "category": "Robotics",
              "student_ids": [s1.id, s2.id]},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["message"] == "Team registered successfully."
    assert body["data"]["members_added"] == 2
    assert set(body["data"]["team"]) == _TEAM_FIELDS
    assert body["data"]["team"]["team_name"] == name
    team_id = body["data"]["team"]["id"]
    members = client_with_uow.get(f"/api/v1/teams/{team_id}/members", headers=mock_admin_headers).json()["data"]["members"]
    assert sorted(m["amount_due"] for m in members) == [120.0, 120.0]


def test_register_team_unknown_competition(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    r = client_with_uow.post(
        "/api/v1/teams", headers=mock_admin_headers,
        json={"competition_id": 999999999, "team_name": "x", "category": "Robotics", "student_ids": [1]},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "NotFoundError"
    assert r.json()["message"] == "Competition 999999999 not found."


def test_register_team_duplicate_name_is_409(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    comp = _make_competition(db_session)
    existing = _make_team(db_session, comp.id, team_name="Same Name", category="Robotics")
    student = _make_student(db_session)

    r = client_with_uow.post(
        "/api/v1/teams", headers=mock_admin_headers,
        json={"competition_id": comp.id, "team_name": "same name", "category": "Robotics",
              "student_ids": [student.id]},
    )

    assert r.status_code == 409
    assert r.json()["error"] == "ConflictError"
    assert r.json()["message"] == "A team named 'same name' already exists in this category."
    assert existing.id


def test_register_team_inactive_student_is_409(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    comp = _make_competition(db_session)
    student = _make_student(db_session, status="inactive", full_name="Idle Kid")

    r = client_with_uow.post(
        "/api/v1/teams", headers=mock_admin_headers,
        json={"competition_id": comp.id, "team_name": f"T {_short()}", "category": "Robotics",
              "student_ids": [student.id]},
    )

    assert r.status_code == 409
    assert r.json()["error"] == "BusinessRuleError"
    assert r.json()["message"] == "Student 'Idle Kid' is not active."


def test_register_team_validation(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post(
        "/api/v1/teams", headers=mock_admin_headers,
        json={"competition_id": 1, "team_name": " ", "category": "Robotics"},
    )
    assert r.status_code == 422


# ── GET /teams/{id} ───────────────────────────────────────────────────────────


def test_get_team(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)

    r = client_with_uow.get(f"/api/v1/teams/{team.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert set(r.json()["data"]) == _TEAM_FIELDS
    assert r.json()["data"]["id"] == team.id


def test_get_team_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/teams/999999999", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["message"] == "Team not found"


# ── PUT / PATCH /teams/{id} ───────────────────────────────────────────────────


def test_put_team(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)

    r = client_with_uow.put(
        f"/api/v1/teams/{team.id}", headers=mock_admin_headers, json={"project_name": "Rover"}
    )

    assert r.status_code == 200
    assert r.json()["message"] == "Team updated successfully."
    assert r.json()["data"]["project_name"] == "Rover"


def test_patch_team(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)

    r = client_with_uow.patch(
        f"/api/v1/teams/{team.id}", headers=mock_admin_headers, json={"notes": "n"}
    )

    assert r.status_code == 200
    assert r.json()["data"]["notes"] == "n"


def test_update_team_empty_body_is_400(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)

    r = client_with_uow.patch(f"/api/v1/teams/{team.id}", headers=mock_admin_headers, json={})

    assert r.status_code == 400
    assert r.json()["message"] == "No fields provided for update"


def test_update_team_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.put("/api/v1/teams/999999999", headers=mock_admin_headers, json={"notes": "n"})
    assert r.status_code == 404
    assert r.json()["message"] == "Team not found"


# ── DELETE /teams/{id} ────────────────────────────────────────────────────────


def test_delete_team(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)

    r = client_with_uow.delete(f"/api/v1/teams/{team.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] is True
    assert r.json()["message"] == "Team deleted successfully."
    assert client_with_uow.get(f"/api/v1/teams/{team.id}", headers=mock_admin_headers).status_code == 404


def test_delete_team_with_paid_member_is_409(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id)
    _add_member(db_session, team.id, _make_student(db_session).id, amount_paid=50.0)

    r = client_with_uow.delete(f"/api/v1/teams/{team.id}", headers=mock_admin_headers)

    assert r.status_code == 409
    assert r.json()["error"] == "BusinessRuleError"


# ── GET /students/{id}/competitions ───────────────────────────────────────────


def test_student_competitions(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id, category="AI", subcategory="Junior")
    student = _make_student(db_session)
    _add_member(db_session, team.id, student.id)

    r = client_with_uow.get(f"/api/v1/students/{student.id}/competitions", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"student_id", "competitions"}
    assert data["student_id"] == student.id
    item = data["competitions"][0]
    assert set(item) == {"membership", "team", "category", "subcategory", "competition"}
    assert item["team"]["id"] == team.id
    assert item["category"] == "AI"
    assert item["competition"]["id"] == comp.id


def test_student_competitions_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): unknown student -> 200 empty list."""
    r = client_with_uow.get("/api/v1/students/999999999/competitions", headers=mock_admin_headers)
    assert r.status_code == 200
    assert r.json()["data"] == {"student_id": 999999999, "competitions": []}


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_team_endpoints_require_auth(client):
    assert client.get("/api/v1/teams?competition_id=1").status_code == 401
    assert client.post("/api/v1/teams", json={}).status_code == 401
    assert client.get("/api/v1/teams/1").status_code == 401
    assert client.put("/api/v1/teams/1", json={"notes": "n"}).status_code == 401
    assert client.patch("/api/v1/teams/1", json={"notes": "n"}).status_code == 401
    assert client.delete("/api/v1/teams/1").status_code == 401
    assert client.get("/api/v1/students/1/competitions").status_code == 401
