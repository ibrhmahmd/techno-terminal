"""
tests/test_analytics.py
────────────────────────
Analytics endpoint tests — Phase 10.

Covers all analytics endpoints:
- Academic Analytics (3 endpoints)
- BI Analytics (7 endpoints)
- Financial Analytics (4 endpoints)
- Competition Analytics (1 endpoint)
"""
import pytest
from datetime import date, timedelta


class TestAcademicAnalytics:
    """Tests for /analytics/academics endpoints."""
    
    def test_unpaid_attendees_success(self, client, admin_headers):
        """
        GET /analytics/academics/unpaid-attendees returns unpaid students.
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
    
    def test_group_roster_success(self, client, admin_headers):
        """
        GET /analytics/academics/groups/{id}/roster returns roster.
        """
        response = client.get(
            "/api/v1/analytics/academics/groups/1/roster?level_number=1",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_group_roster_missing_level(self, client, admin_headers):
        """
        GET /analytics/academics/groups/{id}/roster without level_number returns 422.
        """
        response = client.get(
            "/api/v1/analytics/academics/groups/1/roster",
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    def test_attendance_heatmap_success(self, client, admin_headers):
        """
        GET /analytics/academics/groups/{id}/heatmap returns heatmap data.
        """
        response = client.get(
            "/api/v1/analytics/academics/groups/1/heatmap?level_number=1",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestBIAnalytics:
    """Tests for /analytics/bi endpoints."""
    
    def test_enrollment_trend_success(self, client, admin_headers):
        """
        GET /analytics/bi/enrollment-trend returns enrollment trend.
        """
        response = client.get(
            "/api/v1/analytics/bi/enrollment-trend",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_enrollment_trend_with_cutoff(self, client, admin_headers):
        """
        GET /analytics/bi/enrollment-trend with cutoff date.
        """
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        
        response = client.get(
            f"/api/v1/analytics/bi/enrollment-trend?cutoff={cutoff}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_retention_metrics_success(self, client, admin_headers):
        """
        GET /analytics/bi/retention returns retention metrics.
        """
        response = client.get(
            "/api/v1/analytics/bi/retention",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_instructor_performance_success(self, client, admin_headers):
        """
        GET /analytics/bi/instructor-performance returns performance data.
        """
        response = client.get(
            "/api/v1/analytics/bi/instructor-performance",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_retention_funnel_success(self, client, admin_headers):
        """
        GET /analytics/bi/retention-funnel returns level retention funnel.
        """
        response = client.get(
            "/api/v1/analytics/bi/retention-funnel",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_instructor_value_success(self, client, admin_headers):
        """
        GET /analytics/bi/instructor-value returns value matrix.
        """
        response = client.get(
            "/api/v1/analytics/bi/instructor-value",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_schedule_utilization_success(self, client, admin_headers):
        """
        GET /analytics/bi/schedule-utilization returns utilization data.
        """
        response = client.get(
            "/api/v1/analytics/bi/schedule-utilization",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_flight_risk_success(self, client, admin_headers):
        """
        GET /analytics/bi/flight-risk returns at-risk students.
        """
        response = client.get(
            "/api/v1/analytics/bi/flight-risk",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_bi_endpoints_require_admin(self, client):
        """
        All BI endpoints require admin authentication.
        """
        endpoints = [
            "/api/v1/analytics/bi/enrollment-trend",
            "/api/v1/analytics/bi/retention",
            "/api/v1/analytics/bi/instructor-performance",
            "/api/v1/analytics/bi/retention-funnel",
            "/api/v1/analytics/bi/instructor-value",
            "/api/v1/analytics/bi/schedule-utilization",
            "/api/v1/analytics/bi/flight-risk",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"


class TestFinancialAnalytics:
    """Tests for /analytics/finance endpoints."""
    
    def test_revenue_by_date_success(self, client, admin_headers):
        """
        GET /analytics/finance/revenue-by-date returns revenue data.
        """
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        
        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?start={start}&end={end}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_revenue_by_date_missing_params(self, client, admin_headers):
        """
        GET /analytics/finance/revenue-by-date without dates returns 422.
        """
        response = client.get(
            "/api/v1/analytics/finance/revenue-by-date",
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    def test_revenue_by_method_success(self, client, admin_headers):
        """
        GET /analytics/finance/revenue-by-method returns revenue by method.
        """
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        
        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-method?start={start}&end={end}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_outstanding_by_group_success(self, client, admin_headers):
        """
        GET /analytics/finance/outstanding-by-group returns balances.
        """
        response = client.get(
            "/api/v1/analytics/finance/outstanding-by-group",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_top_debtors_success(self, client, admin_headers):
        """
        GET /analytics/finance/top-debtors returns top debtors.
        """
        response = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=10",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_top_debtors_default_limit(self, client, admin_headers):
        """
        GET /analytics/finance/top-debtors with default limit.
        """
        response = client.get(
            "/api/v1/analytics/finance/top-debtors",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_finance_endpoints_require_admin(self, client):
        """
        All finance analytics endpoints require admin authentication.
        """
        endpoints = [
            "/api/v1/analytics/finance/revenue-by-date?start=2024-01-01&end=2024-01-31",
            "/api/v1/analytics/finance/revenue-by-method?start=2024-01-01&end=2024-01-31",
            "/api/v1/analytics/finance/outstanding-by-group",
            "/api/v1/analytics/finance/top-debtors",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"


class TestCompetitionAnalytics:
    """Tests for /analytics/competitions endpoints."""
    
    def test_fee_summary_success(self, client, admin_headers):
        """
        GET /analytics/competitions/fee-summary returns fee summary.
        """
        response = client.get(
            "/api/v1/analytics/competitions/fee-summary",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_fee_summary_requires_admin(self, client):
        """
        GET /analytics/competitions/fee-summary without auth returns 401.
        """
        response = client.get("/api/v1/analytics/competitions/fee-summary")
        
        assert response.status_code == 401


class TestAnalyticsDashboard:
    """Tests for /analytics/dashboard endpoint."""
    
    def test_dashboard_summary_success(self, client, admin_headers):
        """
        GET /analytics/dashboard/summary returns dashboard data.
        """
        response = client.get(
            "/api/v1/analytics/dashboard/summary",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "active_enrollments" in data["data"]
        assert "today_sessions_count" in data["data"]
    
    def test_dashboard_summary_requires_admin(self, client):
        """
        GET /analytics/dashboard/summary without auth returns 401.
        """
        response = client.get("/api/v1/analytics/dashboard/summary")
        
        assert response.status_code == 401
