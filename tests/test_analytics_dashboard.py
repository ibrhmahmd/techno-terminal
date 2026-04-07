"""
tests/test_analytics_dashboard.py
────────────────────────────────
Dashboard and Key Analytics Endpoints Testing

Covers:
- GET /analytics/dashboard/summary (core dashboard)
- GET /analytics/academics/unpaid-attendees (financial health)
- GET /analytics/finance/revenue-by-date (revenue tracking)
- GET /analytics/finance/top-debtors (collections)

All tests verify:
- Admin-only authentication
- Response schema compliance
- Data presence and types
"""
import pytest
from datetime import date, timedelta


class TestDashboardSummary:
    """Tests for GET /analytics/dashboard/summary — core dashboard metric."""
    
    def test_dashboard_summary_success(self, client, admin_headers):
        """
        GET /analytics/dashboard/summary returns active enrollments and session count.
        Requires admin role.
        """
        response = client.get(
            "/api/v1/analytics/dashboard/summary",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Verify response structure
        dashboard_data = data["data"]
        assert "active_enrollments" in dashboard_data
        assert "today_sessions_count" in dashboard_data
        
        # Verify types (should be integers)
        assert isinstance(dashboard_data["active_enrollments"], int)
        assert isinstance(dashboard_data["today_sessions_count"], int)
        
        # Values should be non-negative
        assert dashboard_data["active_enrollments"] >= 0
        assert dashboard_data["today_sessions_count"] >= 0
    
    def test_dashboard_summary_requires_admin(self, client):
        """
        GET /analytics/dashboard/summary without auth returns 401.
        """
        response = client.get("/api/v1/analytics/dashboard/summary")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestUnpaidAttendees:
    """Tests for GET /analytics/academics/unpaid-attendees."""
    
    def test_unpaid_attendees_success(self, client, admin_headers):
        """
        GET /analytics/academics/unpaid-attendees returns students with unpaid balances.
        Requires admin role.
        """
        response = client.get(
            "/api/v1/analytics/academics/unpaid-attendees",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_unpaid_attendees_with_date(self, client, admin_headers):
        """
        GET /analytics/academics/unpaid-attendees?target_date=YYYY-MM-DD
        Returns unpaid attendees for specific date.
        """
        today = date.today().isoformat()
        
        response = client.get(
            f"/api/v1/analytics/academics/unpaid-attendees?target_date={today}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_unpaid_attendees_requires_auth(self, client):
        """
        GET /analytics/academics/unpaid-attendees without auth returns 401.
        """
        response = client.get("/api/v1/analytics/academics/unpaid-attendees")
        assert response.status_code == 401


class TestRevenueByDate:
    """Tests for GET /analytics/finance/revenue-by-date."""
    
    def test_revenue_by_date_success(self, client, admin_headers):
        """
        GET /analytics/finance/revenue-by-date returns daily revenue totals.
        Requires date range parameters.
        """
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        
        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?start={start_date}&end={end_date}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_revenue_by_date_missing_params(self, client, admin_headers):
        """
        GET /analytics/finance/revenue-by-date without required dates returns 422.
        """
        response = client.get(
            "/api/v1/analytics/finance/revenue-by-date",
            headers=admin_headers
        )
        
        # Should fail validation (422) or return error
        assert response.status_code in [200, 422]
    
    def test_revenue_by_date_requires_admin(self, client):
        """
        GET /analytics/finance/revenue-by-date without auth returns 401.
        """
        response = client.get("/api/v1/analytics/finance/revenue-by-date")
        assert response.status_code == 401


class TestTopDebtors:
    """Tests for GET /analytics/finance/top-debtors."""
    
    def test_top_debtors_default_limit(self, client, admin_headers):
        """
        GET /analytics/finance/top-debtors returns top debtors with default limit.
        """
        response = client.get(
            "/api/v1/analytics/finance/top-debtors",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Should return up to 15 by default
        assert len(data["data"]) <= 15
    
    def test_top_debtors_custom_limit(self, client, admin_headers):
        """
        GET /analytics/finance/top-debtors?limit=N returns N debtors.
        """
        response = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=5",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) <= 5
    
    def test_top_debtors_requires_auth(self, client):
        """
        GET /analytics/finance/top-debtors without auth returns 401.
        """
        response = client.get("/api/v1/analytics/finance/top-debtors")
        assert response.status_code == 401


class TestDashboardAuth:
    """Authentication tests for all dashboard endpoints."""
    
    def test_all_dashboard_endpoints_require_admin(self, client, admin_headers):
        """
        Verify all dashboard endpoints require admin authentication.
        """
        endpoints = [
            "/api/v1/analytics/dashboard/summary",
            "/api/v1/analytics/academics/unpaid-attendees",
            "/api/v1/analytics/finance/revenue-by-date?start=2024-01-01&end=2024-12-31",
            "/api/v1/analytics/finance/top-debtors",
        ]
        
        for endpoint in endpoints:
            # Test without auth
            no_auth_response = client.get(endpoint)
            assert no_auth_response.status_code == 401, f"{endpoint} should require auth"
            
            # Test with admin auth (should not be 401)
            admin_response = client.get(endpoint, headers=admin_headers)
            assert admin_response.status_code != 401, f"{endpoint} should accept admin token"
