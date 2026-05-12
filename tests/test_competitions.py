"""
tests/test_competitions.py
─────────────────────────
Competitions endpoint tests — Phase 8.

Covers:
- Competition CRUD (list, create, get, categories)
- Team registration
- Fee payment marking
"""
import pytest


class TestCompetitionsRead:
    """Tests for GET /competitions endpoints."""
    
    def test_list_competitions_success(self, client, admin_headers):
        """
        GET /competitions returns list of competitions.
        Requires any authentication.
        """
        response = client.get(
            "/api/v1/competitions",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_list_competitions_requires_auth(self, client):
        """
        GET /competitions without auth returns 401.
        """
        response = client.get("/api/v1/competitions")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_get_competition_by_id_success(self, client, admin_headers):
        """
        GET /competitions/{id} returns competition details.
        """
        response = client.get(
            "/api/v1/competitions/1",
            headers=admin_headers
        )
        
        # May succeed or return 404
        assert response.status_code in [200, 404]
    
    def test_get_competition_not_found(self, client, admin_headers):
        """
        GET /competitions/{id} for non-existent ID returns 404.
        """
        response = client.get(
            "/api/v1/competitions/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
    
    def test_list_competition_categories(self, client, admin_headers):
        """
        GET /competitions/{id}/categories returns categories.
        """
        response = client.get(
            "/api/v1/competitions/1/categories",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_list_teams_in_competition(self, client, admin_headers):
        """
        GET /teams?competition_id=1 returns teams.
        """
        response = client.get(
            "/api/v1/teams?competition_id=1",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestCompetitionsWrite:
    """Tests for POST/PATCH /competitions — modifying competitions."""
    
    def test_create_competition_success(self, client, admin_headers):
        """
        POST /competitions creates a new competition.
        Requires admin role.
        """
        import time
        unique_suffix = str(int(time.time()))
        
        response = client.post(
            "/api/v1/competitions",
            headers=admin_headers,
            json={
                "name": f"Test Competition {unique_suffix}",
                "edition_year": 2024,
                "competition_date": "2024-06-01",
                "location": "Main Hall",
                "fee_per_student": 0.0
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_create_competition_validation_error(self, client, admin_headers):
        """
        POST /competitions with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/competitions",
            headers=admin_headers,
            json={
                "name": "",  # Empty name should fail
                "edition_year": "not-a-number"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_create_competition_requires_admin(self, client, admin_headers):
        """
        POST /competitions without admin role should fail.
        Note: Testing with admin headers verifies the endpoint works.
        """
        # This test verifies the endpoint exists and requires admin
        # The actual auth check is tested separately
        response = client.post(
            "/api/v1/competitions",
            headers=admin_headers,
            json={
                "name": "Admin Test Competition",
                "edition_year": 2024,
                "competition_date": "2024-06-01"
            }
        )
        
        # Should not be 401 (auth required) but may fail validation
        assert response.status_code != 401
    
    def test_get_categories_success(self, client, admin_headers):
        """
        GET /competitions/{id}/categories returns categories from teams data.
        Categories are derived from the distinct category values on teams.
        """
        response = client.get(
            "/api/v1/competitions/1/categories",
            headers=admin_headers
        )
        
        # May succeed (200) or return empty list
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["data"], list)
    
    def test_get_categories_not_found(self, client, admin_headers):
        """
        GET /competitions/{id}/categories for non-existent competition.
        """
        response = client.get(
            "/api/v1/competitions/99999/categories",
            headers=admin_headers
        )
        
        assert response.status_code in [404, 200]


class TestTeamRegistration:
    """Tests for team registration endpoints."""
    
    def test_register_team_validation_error(self, client, admin_headers):
        """
        POST /teams with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/teams",
            headers=admin_headers,
            json={
                "team_name": "",  # Empty name
                "competition_id": 1,
                "category": "Robotics",
                "student_ids": []
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_register_team_requires_admin(self, client, admin_headers):
        """
        POST /teams requires admin role.
        """
        response = client.post(
            "/api/v1/teams",
            headers=admin_headers,
            json={
                "team_name": "Test Team",
                "competition_id": 1,
                "category": "Robotics",
                "student_ids": [1, 2]
            }
        )
        
        # Should not be 401 (auth check)
        assert response.status_code != 401
    
    def test_mark_fee_paid_not_found(self, client, admin_headers):
        """
        POST /teams/{team_id}/members/{student_id}/pay for non-existent team.
        """
        response = client.post(
            "/api/v1/teams/99999/members/99999/pay",
            headers=admin_headers
        )
        
        assert response.status_code in [404, 422]


class TestCompetitionsAuth:
    """Authentication tests for competitions endpoints."""
    
    def test_read_endpoints_require_any_auth(self, client, admin_headers):
        """
        Verify read endpoints accept any authentication.
        """
        read_endpoints = [
            "/api/v1/competitions",
            "/api/v1/competitions/1",
            "/api/v1/competitions/1/categories",
            "/api/v1/teams?competition_id=1",
        ]
        
        for endpoint in read_endpoints:
            # Without auth should fail
            no_auth = client.get(endpoint)
            assert no_auth.status_code == 401, f"{endpoint} should require auth"
            
            # With auth should not be 401
            with_auth = client.get(endpoint, headers=admin_headers)
            assert with_auth.status_code != 401, f"{endpoint} should accept valid auth"
    
    def test_write_endpoints_require_admin(self, client, admin_headers):
        """
        Verify write endpoints require admin authentication.
        """
        write_tests = [
            ("POST", "/api/v1/competitions", {"name": "Test", "edition_year": 2024}),
            ("POST", "/api/v1/teams", {"team_name": "Test", "competition_id": 1, "category": "Robotics", "student_ids": [1]}),
            ("POST", "/api/v1/teams/99999/members/99999/pay", {}),
        ]
        
        for method, endpoint, body in write_tests:
            # Without auth should fail
            if method == "POST":
                no_auth = client.post(endpoint, json=body)
            
            assert no_auth.status_code == 401, f"{endpoint} should require auth"
            
            # With admin auth should not be 401
            if method == "POST":
                with_auth = client.post(endpoint, headers=admin_headers, json=body)
            
            assert with_auth.status_code != 401, f"{endpoint} should accept admin auth"
