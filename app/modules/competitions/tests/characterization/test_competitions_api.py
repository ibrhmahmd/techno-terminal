"""Characterization tests for the Competitions HTTP API (ticket #21).

Pins status codes, envelopes and field shapes of the eight endpoints served by
``app/api/routers/competitions/competitions_router.py`` BEFORE the HTTP layer
moves into ``app/modules/competitions/api/``:

    GET/POST /competitions, GET/PUT/PATCH/DELETE /competitions/{id},
    GET /competitions/{id}/summary, GET /competitions/{id}/categories

Buckets
-------
* ``CompetitionService`` opens its own ``get_session()`` and really commits, so
  every row is seeded through the committed ``db_session`` (uuid-tagged) and list
  endpoints are searched with the id, never by page position.
* No notifications are scheduled by these routes.

Pinned quirks (pinned, not endorsed)
------------------------------------
* PUT and PATCH are the same handler: both accept partial bodies.
* PUT/PATCH with an empty (all-None) body is a 400 HTTPException envelope.
* ``edition_year`` on create is derived from ``competition_date`` (None when no
  date is given, which the database then rejects).
"""

import uuid
from datetime import date

from app.modules.competitions.models import Competition, Team


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_competition(db_session, **overrides) -> Competition:
    comp = Competition(
        name=overrides.pop("name", f"Comp {_short()}"),
        edition=overrides.pop("edition", None),
        edition_year=overrides.pop("edition_year", 2026),
        competition_date=overrides.pop("competition_date", date(2026, 5, 1)),
        location=overrides.pop("location", "Cairo"),
        notes=overrides.pop("notes", None),
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


_COMP_FIELDS = {
    "id", "name", "edition", "edition_year", "competition_date",
    "location", "notes", "fee_per_student", "created_at",
}


# ── GET /competitions ─────────────────────────────────────────────────────────


def test_list_competitions(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)

    r = client_with_uow.get("/api/v1/competitions", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    mine = [c for c in body["data"] if c["id"] == comp.id]
    assert len(mine) == 1
    assert set(mine[0]) == _COMP_FIELDS
    assert mine[0]["name"] == comp.name
    assert mine[0]["edition_year"] == 2026
    assert mine[0]["competition_date"] == "2026-05-01"
    assert mine[0]["fee_per_student"] == 100.0


# ── POST /competitions ────────────────────────────────────────────────────────


def test_create_competition(client_with_uow, override_auth, mock_admin_headers):
    name = f"Created {_short()}"
    r = client_with_uow.post(
        "/api/v1/competitions",
        headers=mock_admin_headers,
        json={"name": name, "competition_date": "2027-03-10", "location": "Giza", "fee_per_student": 75},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Competition created successfully."
    assert set(body["data"]) == _COMP_FIELDS
    assert body["data"]["name"] == name
    assert body["data"]["edition_year"] == 2027
    assert body["data"]["fee_per_student"] == 75.0


def test_create_competition_blank_name_is_422(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post("/api/v1/competitions", headers=mock_admin_headers, json={"name": "  "})
    assert r.status_code == 422
    assert r.json()["success"] is False


# ── GET /competitions/{id} ────────────────────────────────────────────────────


def test_get_competition(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)

    r = client_with_uow.get(f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"]["id"] == comp.id


def test_get_competition_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/competitions/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == "Competition not found"


# ── PUT / PATCH /competitions/{id} ────────────────────────────────────────────


def test_put_competition_updates_given_fields(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)

    r = client_with_uow.put(
        f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers,
        json={"location": "Alexandria"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Competition updated successfully."
    assert body["data"]["location"] == "Alexandria"
    assert body["data"]["name"] == comp.name


def test_patch_competition_same_behaviour(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)

    r = client_with_uow.patch(
        f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers,
        json={"notes": "patched"},
    )

    assert r.status_code == 200
    assert r.json()["data"]["notes"] == "patched"


def test_update_competition_empty_body_is_400(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)

    r = client_with_uow.patch(f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers, json={})

    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert body["message"] == "No fields provided for update"


def test_update_competition_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.put(
        "/api/v1/competitions/999999999", headers=mock_admin_headers, json={"location": "X"}
    )
    assert r.status_code == 404
    assert r.json()["message"] == "Competition not found"


def test_update_competition_validation(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    r = client_with_uow.patch(
        f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers, json={"edition_year": 1999}
    )
    assert r.status_code == 422


# ── DELETE /competitions/{id} ─────────────────────────────────────────────────


def test_delete_competition(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)

    r = client_with_uow.delete(f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["data"] is True
    assert body["message"] == "Competition deleted successfully."
    assert client_with_uow.get(f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers).status_code == 404


def test_delete_competition_with_teams_is_409(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    _make_team(db_session, comp.id)

    r = client_with_uow.delete(f"/api/v1/competitions/{comp.id}", headers=mock_admin_headers)

    assert r.status_code == 409
    body = r.json()
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Cannot delete competition that has teams. Delete teams first."


def test_delete_competition_unknown_id(client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): 200 with data=False and the success message."""
    r = client_with_uow.delete("/api/v1/competitions/999999999", headers=mock_admin_headers)
    assert r.status_code == 200
    assert r.json() == {"success": True, "data": False, "message": "Competition deleted successfully."}


# ── GET /competitions/{id}/summary ────────────────────────────────────────────


def test_competition_summary(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    team = _make_team(db_session, comp.id, category="Robotics", subcategory="Junior")

    r = client_with_uow.get(f"/api/v1/competitions/{comp.id}/summary", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"competition", "categories", "total_teams", "total_participants"}
    assert data["competition"]["id"] == comp.id
    assert data["total_teams"] == 1
    assert data["total_participants"] == 0
    cat = data["categories"][0]
    assert set(cat) == {"category", "subcategory", "teams"}
    assert cat["category"] == "Robotics"
    assert cat["subcategory"] == "Junior"
    assert cat["teams"][0]["team"]["id"] == team.id
    assert cat["teams"][0]["members"] == []


def test_competition_summary_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/competitions/999999999/summary", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["message"] == "Competition not found"


# ── GET /competitions/{id}/categories ─────────────────────────────────────────


def test_list_categories(client_with_uow, override_auth, mock_admin_headers, db_session):
    comp = _make_competition(db_session)
    _make_team(db_session, comp.id, category="Robotics", subcategory="Junior")
    _make_team(db_session, comp.id, category="Robotics", subcategory="Senior")
    _make_team(db_session, comp.id, category="AI")

    r = client_with_uow.get(f"/api/v1/competitions/{comp.id}/categories", headers=mock_admin_headers)

    assert r.status_code == 200
    data = {c["category"]: sorted(c["subcategories"]) for c in r.json()["data"]}
    assert data == {"Robotics": ["Junior", "Senior"], "AI": []}


def test_list_categories_unknown_competition(client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): unknown competition -> 200 empty list."""
    r = client_with_uow.get("/api/v1/competitions/999999999/categories", headers=mock_admin_headers)
    assert r.status_code == 200
    assert r.json()["data"] == []


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_competitions_endpoints_require_auth(client):
    assert client.get("/api/v1/competitions").status_code == 401
    assert client.post("/api/v1/competitions", json={"name": "x"}).status_code == 401
    assert client.get("/api/v1/competitions/1").status_code == 401
    assert client.put("/api/v1/competitions/1", json={"location": "x"}).status_code == 401
    assert client.patch("/api/v1/competitions/1", json={"location": "x"}).status_code == 401
    assert client.delete("/api/v1/competitions/1").status_code == 401
    assert client.get("/api/v1/competitions/1/summary").status_code == 401
    assert client.get("/api/v1/competitions/1/categories").status_code == 401
