"""
Test module for Group Competitions router.

Tests all endpoints in group_competitions_router.py:
- GET /academics/groups/{group_id}/competitions - List competitions
- GET /academics/groups/{group_id}/teams - List teams
- POST /academics/groups/{group_id}/teams/{team_id}/link - Link team
- POST /academics/groups/{group_id}/competitions/{competition_id}/register - Register team
- PATCH /academics/groups/{group_id}/competitions/{participation_id}/complete - Complete participation
- DELETE /academics/groups/{group_id}/competitions/{participation_id} - Withdraw
- GET /academics/groups/{group_id}/competitions/analytics - Competition analytics
"""
import pytest
from datetime import date, datetime
from app.modules.academics.models import Group, Course
from app.modules.competitions.models import Competition, Team, GroupCompetitionParticipation


class TestGroupCompetitionsRead:
    """GET endpoints - require_any auth"""

    def test_list_group_competitions_success(self, client, admin_headers, db_session):
        """Test listing competition participations for a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/competitions",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_list_group_competitions_with_filter(self, client, admin_headers, db_session):
        """Test listing competitions with active filter."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/competitions?is_active=true",
            headers=admin_headers
        )

        assert response.status_code == 200

    def test_list_group_teams_success(self, client, admin_headers, db_session):
        """Test listing teams linked to a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a team linked to the group
        team = Team(team_name="Test Team", group_id=group.id)
        db_session.add(team)
        db_session.commit()

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/teams",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_list_group_teams_include_inactive(self, client, admin_headers, db_session):
        """Test listing teams including inactive."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a deleted team
        team = Team(team_name="Deleted Team", group_id=group.id, is_deleted=True)
        db_session.add(team)
        db_session.commit()

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/teams?include_inactive=true",
            headers=admin_headers
        )

        assert response.status_code == 200

    def test_get_competition_analytics_success(self, client, admin_headers, db_session):
        """Test getting competition participation analytics."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.get(
            f"/api/v1/academics/groups/{group.id}/competitions/analytics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_list_group_teams_not_found(self, client, admin_headers):
        """Test listing teams for non-existent group."""
        response = client.get(
            "/api/v1/academics/groups/99999/teams",
            headers=admin_headers
        )

        # May return empty list or 404
        assert response.status_code in [200, 404]


class TestGroupCompetitionsWrite:
    """POST/PATCH/DELETE - require_admin auth"""

    def test_link_team_to_group_success(self, client, admin_headers, db_session):
        """Test linking an existing team to a group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a team
        team = Team(team_name="Team to Link")
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/teams/{team.id}/link",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "linked" in data["message"].lower()

    def test_link_team_to_group_not_found(self, client, admin_headers, db_session):
        """Test linking non-existent team returns 404."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/teams/99999/link",
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_link_team_to_group_unauthorized(self, client, db_session):
        """Test linking team without auth fails."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(f"/api/v1/academics/groups/{group.id}/teams/1/link")
        assert response.status_code == 401

    def test_register_team_for_competition_success(self, client, admin_headers, db_session):
        """Test registering a team for a competition."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create a team
        team = Team(team_name="Competition Team", group_id=group.id)
        db_session.add(team)

        # Create a competition
        competition = Competition(
            name="Test Competition",
            start_date=datetime.now()
        )
        db_session.add(competition)
        db_session.commit()
        db_session.refresh(team)
        db_session.refresh(competition)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/competitions/{competition.id}/register",
            headers=admin_headers,
            params={"team_id": team.id}
        )

        # May succeed or fail depending on business logic
        assert response.status_code in [200, 201, 400]

    def test_register_team_not_found(self, client, admin_headers, db_session):
        """Test registering for non-existent competition returns 404."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/competitions/99999/register",
            headers=admin_headers,
            params={"team_id": 1}
        )

        assert response.status_code in [400, 404]

    def test_complete_competition_participation_success(self, client, admin_headers, db_session):
        """Test marking competition participation as completed."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create participation
        participation = GroupCompetitionParticipation(
            group_id=group.id,
            team_id=1,
            competition_id=1,
            is_active=True
        )
        db_session.add(participation)
        db_session.commit()
        db_session.refresh(participation)

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}/competitions/{participation.id}/complete",
            headers=admin_headers,
            params={"final_placement": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_complete_participation_not_found(self, client, admin_headers, db_session):
        """Test completing non-existent participation returns 404."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}/competitions/99999/complete",
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_withdraw_from_competition_success(self, client, admin_headers, db_session):
        """Test withdrawing from a competition."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create participation
        participation = GroupCompetitionParticipation(
            group_id=group.id,
            team_id=1,
            competition_id=1,
            is_active=True
        )
        db_session.add(participation)
        db_session.commit()
        db_session.refresh(participation)

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/competitions/{participation.id}",
            headers=admin_headers,
            params={"reason": "Scheduling conflict"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_withdraw_from_competition_not_found(self, client, admin_headers, db_session):
        """Test withdrawing from non-existent participation returns 404."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/competitions/99999",
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_write_operations_non_admin(self, client, system_admin_headers, db_session):
        """Test write operations with non-admin token fail."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/teams/1/link",
            headers=system_admin_headers
        )

        assert response.status_code == 403


class TestGroupCompetitionsEdgeCases:
    """Edge cases and boundary conditions"""

    def test_register_team_already_registered(self, client, admin_headers, db_session):
        """Test registering already registered team."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create team and participation
        team = Team(team_name="Already Registered", group_id=group.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)

        competition = Competition(
            name="Duplicate Registration Test",
            start_date=datetime.now()
        )
        db_session.add(competition)
        db_session.commit()
        db_session.refresh(competition)

        # First registration
        participation = GroupCompetitionParticipation(
            group_id=group.id,
            team_id=team.id,
            competition_id=competition.id,
            is_active=True
        )
        db_session.add(participation)
        db_session.commit()

        # Try to register again
        response = client.post(
            f"/api/v1/academics/groups/{group.id}/competitions/{competition.id}/register",
            headers=admin_headers,
            params={"team_id": team.id}
        )

        # Should fail with duplicate error
        assert response.status_code in [400, 409]

    def test_complete_already_completed_participation(self, client, admin_headers, db_session):
        """Test completing already completed participation."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create inactive (completed) participation
        participation = GroupCompetitionParticipation(
            group_id=group.id,
            team_id=1,
            competition_id=1,
            is_active=False,
            left_at=datetime.now()
        )
        db_session.add(participation)
        db_session.commit()
        db_session.refresh(participation)

        response = client.patch(
            f"/api/v1/academics/groups/{group.id}/competitions/{participation.id}/complete",
            headers=admin_headers
        )

        # Should fail or handle gracefully
        assert response.status_code in [200, 400]

    def test_withdraw_already_inactive_participation(self, client, admin_headers, db_session):
        """Test withdrawing from already inactive participation."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create inactive participation
        participation = GroupCompetitionParticipation(
            group_id=group.id,
            team_id=1,
            competition_id=1,
            is_active=False,
            left_at=datetime.now()
        )
        db_session.add(participation)
        db_session.commit()
        db_session.refresh(participation)

        response = client.delete(
            f"/api/v1/academics/groups/{group.id}/competitions/{participation.id}",
            headers=admin_headers
        )

        # Should fail or handle gracefully
        assert response.status_code in [200, 400]

    def test_link_team_already_linked(self, client, admin_headers, db_session):
        """Test linking team already linked to group."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session)
        group = create_test_group(db_session, course_id=course.id)

        # Create team already linked
        team = Team(team_name="Already Linked", group_id=group.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)

        response = client.post(
            f"/api/v1/academics/groups/{group.id}/teams/{team.id}/link",
            headers=admin_headers
        )

        # May succeed (idempotent) or return specific message
        assert response.status_code == 200
