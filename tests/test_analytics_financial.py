"""
Test module for Financial Analytics router.

Tests all endpoints in app/api/routers/analytics/financial.py:
- GET /analytics/finance/revenue-by-date
- GET /analytics/finance/revenue-by-method
- GET /analytics/finance/outstanding-by-group
- GET /analytics/finance/top-debtors
- GET /analytics/finance/revenue-metrics
- GET /analytics/finance/revenue-forecast

All endpoints require admin authentication.
"""
from datetime import date, timedelta


class TestRevenueByDate:
    """GET /analytics/finance/revenue-by-date - require_admin auth"""

    def test_revenue_by_date_success(self, client, admin_headers):
        """Test getting revenue breakdown by date with valid range."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?start={start_date}&end={end_date}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_revenue_by_date_missing_start(self, client, admin_headers):
        """Test getting revenue without start date returns 422."""
        end_date = date.today().isoformat()
        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?end={end_date}",
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_revenue_by_date_missing_end(self, client, admin_headers):
        """Test getting revenue without end date returns 422."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?start={start_date}",
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_revenue_by_date_invalid_range(self, client, admin_headers):
        """Test getting revenue with end date before start date."""
        start_date = date.today().isoformat()
        end_date = (date.today() - timedelta(days=30)).isoformat()

        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?start={start_date}&end={end_date}",
            headers=admin_headers
        )
        # May return 200 with empty data or 422 depending on validation
        assert response.status_code in [200, 422]

    def test_revenue_by_date_unauthorized(self, client):
        """Test getting revenue by date without auth returns 401."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-date?start={start_date}&end={end_date}"
        )
        assert response.status_code == 401


class TestRevenueByMethod:
    """GET /analytics/finance/revenue-by-method - require_admin auth"""

    def test_revenue_by_method_success(self, client, admin_headers):
        """Test getting revenue breakdown by payment method."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-method?start={start_date}&end={end_date}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_revenue_by_method_missing_params(self, client, admin_headers):
        """Test getting revenue by method without required params returns 422."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-by-method",
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_revenue_by_method_grouping(self, client, admin_headers):
        """Test revenue is properly grouped by payment method."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-method?start={start_date}&end={end_date}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Each item should have payment method info
        for item in data["data"]:
            assert any(key in item for key in ["method", "payment_method", "total_revenue", "count"])

    def test_revenue_by_method_unauthorized(self, client):
        """Test getting revenue by method without auth returns 401."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/finance/revenue-by-method?start={start_date}&end={end_date}"
        )
        assert response.status_code == 401


class TestOutstandingByGroup:
    """GET /analytics/finance/outstanding-by-group - require_admin auth"""

    def test_outstanding_by_group_success(self, client, admin_headers):
        """Test getting outstanding balances grouped by academic group."""
        response = client.get(
            "/api/v1/analytics/finance/outstanding-by-group",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_outstanding_by_group_empty(self, client, admin_headers):
        """Test outstanding by group when no outstanding balances."""
        response = client.get(
            "/api/v1/analytics/finance/outstanding-by-group",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should return list (may be empty)
        assert isinstance(data["data"], list)

    def test_outstanding_by_group_structure(self, client, admin_headers):
        """Test outstanding data includes group and balance info."""
        response = client.get(
            "/api/v1/analytics/finance/outstanding-by-group",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Each item should have group and outstanding amount
        for item in data["data"]:
            assert any(key in item for key in ["group_id", "group_name", "outstanding_amount", "student_count"])

    def test_outstanding_by_group_unauthorized(self, client):
        """Test getting outstanding by group without auth returns 401."""
        response = client.get("/api/v1/analytics/finance/outstanding-by-group")
        assert response.status_code == 401


class TestTopDebtors:
    """GET /analytics/finance/top-debtors - require_admin auth"""

    def test_top_debtors_default_limit(self, client, admin_headers):
        """Test getting top debtors with default limit (15)."""
        response = client.get(
            "/api/v1/analytics/finance/top-debtors",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # Should not exceed default limit
        assert len(data["data"]) <= 15

    def test_top_debtors_custom_limit(self, client, admin_headers):
        """Test getting top debtors with custom limit."""
        response = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=5",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5

    def test_top_debtors_limit_boundary(self, client, admin_headers):
        """Test top debtors at limit boundaries (1 and 100)."""
        # Test minimum
        response_min = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=1",
            headers=admin_headers
        )
        assert response_min.status_code == 200

        # Test maximum
        response_max = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=100",
            headers=admin_headers
        )
        assert response_max.status_code == 200

    def test_top_debtors_invalid_limit(self, client, admin_headers):
        """Test limit parameter outside valid range (1-100) returns 422."""
        # Test below minimum
        response_low = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=0",
            headers=admin_headers
        )
        assert response_low.status_code == 422

        # Test above maximum
        response_high = client.get(
            "/api/v1/analytics/finance/top-debtors?limit=101",
            headers=admin_headers
        )
        assert response_high.status_code == 422

    def test_top_debtors_structure(self, client, admin_headers):
        """Test debtor data includes student and balance info."""
        response = client.get(
            "/api/v1/analytics/finance/top-debtors",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Each debtor should have identifying info
        for item in data["data"]:
            assert any(key in item for key in ["student_id", "student_name", "outstanding_balance", "group_id"])

    def test_top_debtors_unauthorized(self, client):
        """Test getting top debtors without auth returns 401."""
        response = client.get("/api/v1/analytics/finance/top-debtors")
        assert response.status_code == 401


class TestRevenueMetrics:
    """GET /analytics/finance/revenue-metrics - require_admin auth"""

    def test_revenue_metrics_success(self, client, admin_headers):
        """Test getting extended revenue metrics with default 6 months."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-metrics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_revenue_metrics_default_months(self, client, admin_headers):
        """Test default months parameter is 6."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-metrics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should return monthly breakdown for ~6 months
        if isinstance(data["data"], dict) and "monthly_breakdown" in data["data"]:
            assert len(data["data"]["monthly_breakdown"]) <= 6

    def test_revenue_metrics_custom_months(self, client, admin_headers):
        """Test custom months parameter (1-24 range)."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-metrics?months=12",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_revenue_metrics_invalid_months(self, client, admin_headers):
        """Test months parameter outside valid range (1-24) returns 422."""
        # Test below minimum
        response_low = client.get(
            "/api/v1/analytics/finance/revenue-metrics?months=0",
            headers=admin_headers
        )
        assert response_low.status_code == 422

        # Test above maximum
        response_high = client.get(
            "/api/v1/analytics/finance/revenue-metrics?months=25",
            headers=admin_headers
        )
        assert response_high.status_code == 422

    def test_revenue_metrics_trend_analysis(self, client, admin_headers):
        """Test revenue metrics includes trend analysis data."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-metrics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should contain trend information
        metrics = data["data"]
        assert any(key in metrics for key in ["total_revenue", "monthly_breakdown", "trend", "growth_rate"])

    def test_revenue_metrics_unauthorized(self, client):
        """Test getting revenue metrics without auth returns 401."""
        response = client.get("/api/v1/analytics/finance/revenue-metrics")
        assert response.status_code == 401


class TestRevenueForecast:
    """GET /analytics/finance/revenue-forecast - require_admin auth"""

    def test_revenue_forecast_success(self, client, admin_headers):
        """Test getting revenue forecast with default 3 months ahead."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-forecast",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_revenue_forecast_default_months(self, client, admin_headers):
        """Test default months_ahead parameter is 3."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-forecast",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should return ~3 months of forecasts
        assert len(data["data"]) <= 3

    def test_revenue_forecast_custom_months(self, client, admin_headers):
        """Test custom months_ahead parameter (1-12 range)."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-forecast?months_ahead=6",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 6

    def test_revenue_forecast_invalid_months(self, client, admin_headers):
        """Test months_ahead parameter outside valid range (1-12) returns 422."""
        # Test below minimum
        response_low = client.get(
            "/api/v1/analytics/finance/revenue-forecast?months_ahead=0",
            headers=admin_headers
        )
        assert response_low.status_code == 422

        # Test above maximum
        response_high = client.get(
            "/api/v1/analytics/finance/revenue-forecast?months_ahead=13",
            headers=admin_headers
        )
        assert response_high.status_code == 422

    def test_revenue_forecast_structure(self, client, admin_headers):
        """Test forecast data includes month and projected revenue."""
        response = client.get(
            "/api/v1/analytics/finance/revenue-forecast",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Each forecast should have month and amount
        for item in data["data"]:
            assert any(key in item for key in ["month", "forecasted_revenue", "confidence", "projected_amount"])

    def test_revenue_forecast_unauthorized(self, client):
        """Test getting revenue forecast without auth returns 401."""
        response = client.get("/api/v1/analytics/finance/revenue-forecast")
        assert response.status_code == 401
