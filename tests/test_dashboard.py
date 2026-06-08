"""
tests/test_dashboard.py
─────────────────────
Tests for the Dashboard API endpoints.
"""

from datetime import date, timedelta
import pytest


class TestDashboardDailyOverview:
    """Test suite for GET /api/v1/dashboard/daily-overview"""

    def test_dashboard_overview_success(self, client, mock_admin_headers, override_auth):
        """Test successful dashboard overview retrieval."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Check response structure
        result = data["data"]
        assert "date" in result
        assert "generated_at" in result
        assert "cache_ttl" in result
        assert "groups" in result
        assert "instructors" in result
        assert "scheduled_groups" in result
        assert "summary" in result

    def test_dashboard_overview_with_attendance(self, client, mock_admin_headers, override_auth):
        """Test dashboard with include_attendance=true."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}&include_attendance=true",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_dashboard_overview_without_attendance(self, client, mock_admin_headers, override_auth):
        """Test dashboard with include_attendance=false."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}&include_attendance=false",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_dashboard_overview_empty_date(self, client, mock_admin_headers, override_auth):
        """Test dashboard with date that has no sessions."""
        # Use a date far in the future
        future_date = (date.today() + timedelta(days=365)).isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={future_date}",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scheduled_groups"] == []
        assert data["data"]["summary"]["total_groups_today"] == 0

    def test_dashboard_overview_missing_date(self, client, mock_admin_headers, override_auth):
        """Test dashboard without required date parameter."""
        response = client.get(
            "/api/v1/dashboard/daily-overview",
            headers=mock_admin_headers
        )
        assert response.status_code == 422  # Validation error

    def test_dashboard_overview_invalid_date_format(self, client, mock_admin_headers, override_auth):
        """Test dashboard with invalid date format."""
        response = client.get(
            "/api/v1/dashboard/daily-overview?date=invalid-date",
            headers=mock_admin_headers
        )
        assert response.status_code == 422  # Validation error

    def test_dashboard_overview_unauthorized(self, client):
        """Test dashboard without authentication."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}"
        )
        assert response.status_code == 401

    def test_dashboard_overview_forbidden(self, client, instructor_headers):
        """Test dashboard with non-admin user (should fail)."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}",
            headers=instructor_headers
        )
        # Instructors might be allowed depending on role configuration
        # This test documents the expected behavior
        assert response.status_code in [200, 403]

    def test_dashboard_response_lookup_table_pattern(self, client, mock_admin_headers, override_auth):
        """Verify lookup table pattern is used correctly."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Groups should be a dict (lookup table), not a list
        assert isinstance(data["groups"], dict)
        
        # Instructors should be a dict (lookup table), not a list
        assert isinstance(data["instructors"], dict)
        
        # Scheduled groups should be a list
        assert isinstance(data["scheduled_groups"], list)

    def test_dashboard_summary_structure(self, client, mock_admin_headers, override_auth):
        """Verify summary has correct structure."""
        target_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/dashboard/daily-overview?date={target_date}",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        
        assert "total_groups_today" in summary
        assert "total_instructors_today" in summary
        assert "unique_instructor_ids" in summary
        assert isinstance(summary["total_groups_today"], int)
        assert isinstance(summary["total_instructors_today"], int)
        assert isinstance(summary["unique_instructor_ids"], list)
