"""A user who is neither admin nor the team's coach gets 403 ForbiddenError (#225)."""
from app.testing.db_helpers import create_test_competition, create_test_team


def test_get_team_as_non_coach_instructor_is_403(
    client, db_session, override_instructor_auth, instructor_headers
):
    team = create_test_team(db_session, create_test_competition(db_session).id)
    db_session.commit()

    r = client.get(f"/api/v1/teams/{team.id}", headers=instructor_headers)

    assert r.status_code == 403
    assert r.json()["error"] == "ForbiddenError"
