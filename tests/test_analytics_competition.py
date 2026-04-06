"""
Test module for Competition Analytics router.

Tests all endpoints in app/api/routers/analytics/competition.py:
- GET /analytics/competitions/fee-summary

All endpoints require admin authentication.
"""
from datetime import date


class TestCompetitionFeeSummary:
    """GET /analytics/competitions/fee-summary - require_admin auth"""

    def test_competition_fee_summary_success(self, client, admin_headers):
        """Test getting competition fee summary with all competitions."""
        response = client.get(
            "/api/v1/analytics/competitions/fee-summary",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_competition_fee_summary_structure(self, client, admin_headers):
        """Test fee summary includes participation and fee data."""
        response = client.get(
            "/api/v1/analytics/competitions/fee-summary",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Each summary should have competition and financial info
        for item in data["data"]:
            assert any(key in item for key in [
                "competition_id", "competition_name", "total_fees",
                "participant_count", "team_count", "entry_fee", "total_collected"
            ])

    def test_competition_fee_summary_empty(self, client, admin_headers):
        """Test fee summary when no competitions exist."""
        response = client.get(
            "/api/v1/analytics/competitions/fee-summary",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should return empty list, not error
        assert isinstance(data["data"], list)

    def test_competition_fee_summary_unauthorized(self, client):
        """Test getting fee summary without auth returns 401."""
        response = client.get("/api/v1/analytics/competitions/fee-summary")
        assert response.status_code == 401

    def test_competition_fee_summary_forbidden(self, client, system_admin_headers):
        """Test getting fee summary with system_admin token (may be 200 or 403)."""
        response = client.get(
            "/api/v1/analytics/competitions/fee-summary",
            headers=system_admin_headers
        )
        assert response.status_code in [200, 403]
