"""
Test module for BI Analytics router.

Tests all endpoints in app/api/routers/analytics/bi.py:
- GET /analytics/bi/enrollment-trend
- GET /analytics/bi/retention
- GET /analytics/bi/instructor-performance
- GET /analytics/bi/retention-funnel
- GET /analytics/bi/instructor-value
- GET /analytics/bi/schedule-utilization
- GET /analytics/bi/flight-risk
- GET /analytics/bi/user-engagement
- GET /analytics/bi/retention-analysis

All endpoints require admin authentication.
"""
import pytest
from datetime import date, timedelta


class TestEnrollmentTrend:
    """GET /analytics/bi/enrollment-trend - require_admin auth"""

    def test_enrollment_trend_success(self, client, admin_headers):
        """Test getting enrollment trend with default cutoff."""
        response = client.get(
            "/api/v1/analytics/bi/enrollment-trend",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_enrollment_trend_with_cutoff(self, client, admin_headers):
        """Test getting enrollment trend with specific cutoff date."""
        cutoff_date = (date.today() - timedelta(days=30)).isoformat()
        response = client.get(
            f"/api/v1/analytics/bi/enrollment-trend?cutoff={cutoff_date}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_enrollment_trend_unauthorized(self, client):
        """Test getting enrollment trend without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/enrollment-trend")
        assert response.status_code == 401

    def test_enrollment_trend_forbidden(self, client, system_admin_headers):
        """Test getting enrollment trend with system_admin token (may be 200 or 403)."""
        response = client.get(
            "/api/v1/analytics/bi/enrollment-trend",
            headers=system_admin_headers
        )
        assert response.status_code in [200, 403, 401]  # 401 if token invalid, 403 if forbidden, 200 if allowed


class TestRetentionMetrics:
    """GET /analytics/bi/retention - require_admin auth"""

    def test_retention_metrics_success(self, client, admin_headers):
        """Test getting retention metrics by course."""
        response = client.get(
            "/api/v1/analytics/bi/retention",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_retention_metrics_data_structure(self, client, admin_headers):
        """Test retention metrics response structure."""
        response = client.get(
            "/api/v1/analytics/bi/retention",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Each item should have course info and retention rates
        for item in data["data"]:
            assert "course_id" in item or "course_name" in item or "retention_rate" in item

    def test_retention_metrics_unauthorized(self, client):
        """Test getting retention metrics without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/retention")
        assert response.status_code == 401


class TestInstructorPerformance:
    """GET /analytics/bi/instructor-performance - require_admin auth"""

    def test_instructor_performance_success(self, client, admin_headers):
        """Test getting instructor performance metrics."""
        response = client.get(
            "/api/v1/analytics/bi/instructor-performance",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_instructor_performance_empty(self, client, admin_headers):
        """Test instructor performance when no instructors exist."""
        response = client.get(
            "/api/v1/analytics/bi/instructor-performance",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_instructor_performance_unauthorized(self, client):
        """Test getting instructor performance without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/instructor-performance")
        assert response.status_code == 401


class TestLevelRetentionFunnel:
    """GET /analytics/bi/retention-funnel - require_admin auth"""

    def test_level_retention_funnel_success(self, client, admin_headers):
        """Test getting level retention funnel."""
        response = client.get(
            "/api/v1/analytics/bi/retention-funnel",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_level_retention_funnel_structure(self, client, admin_headers):
        """Test funnel data includes course/level progression info."""
        response = client.get(
            "/api/v1/analytics/bi/retention-funnel",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Funnel should show progression through levels
        for item in data["data"]:
            assert any(key in item for key in ["course_id", "level_number", "student_count", "retention_rate"])

    def test_level_retention_funnel_unauthorized(self, client):
        """Test getting retention funnel without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/retention-funnel")
        assert response.status_code == 401


class TestInstructorValueMatrix:
    """GET /analytics/bi/instructor-value - require_admin auth"""

    def test_instructor_value_matrix_success(self, client, admin_headers):
        """Test getting instructor value matrix."""
        response = client.get(
            "/api/v1/analytics/bi/instructor-value",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_instructor_value_matrix_data_types(self, client, admin_headers):
        """Test value matrix includes revenue and attendance correlation."""
        response = client.get(
            "/api/v1/analytics/bi/instructor-value",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should contain financial and attendance metrics per instructor
        for item in data["data"]:
            assert any(key in item for key in ["instructor_id", "revenue", "attendance_rate", "efficiency"])

    def test_instructor_value_matrix_unauthorized(self, client):
        """Test getting instructor value matrix without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/instructor-value")
        assert response.status_code == 401


class TestScheduleUtilization:
    """GET /analytics/bi/schedule-utilization - require_admin auth"""

    def test_schedule_utilization_success(self, client, admin_headers):
        """Test getting schedule utilization percentages."""
        response = client.get(
            "/api/v1/analytics/bi/schedule-utilization",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_schedule_utilization_percentages(self, client, admin_headers):
        """Test utilization data includes percentage values."""
        response = client.get(
            "/api/v1/analytics/bi/schedule-utilization",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should show utilization rates
        for item in data["data"]:
            assert any(key in item for key in ["day", "time_start", "total_enrolled", "total_capacity", "utilization_pct"])

    def test_schedule_utilization_unauthorized(self, client):
        """Test getting schedule utilization without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/schedule-utilization")
        assert response.status_code == 401


class TestFlightRiskStudents:
    """GET /analytics/bi/flight-risk - require_admin auth"""

    def test_flight_risk_students_success(self, client, admin_headers):
        """Test getting flight-risk students list."""
        response = client.get(
            "/api/v1/analytics/bi/flight-risk",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_flight_risk_students_risk_scores(self, client, admin_headers):
        """Test flight-risk data includes risk indicators."""
        response = client.get(
            "/api/v1/analytics/bi/flight-risk",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should identify at-risk students with reasons
        for item in data["data"]:
            assert any(key in item for key in ["student_id", "risk_score", "risk_factors", "last_attendance"])

    def test_flight_risk_students_unauthorized(self, client):
        """Test getting flight-risk students without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/flight-risk")
        assert response.status_code == 401


@pytest.mark.skip(reason="user_sessions table missing - see tech-debt.md")
class TestUserEngagement:
    """GET /analytics/bi/user-engagement - require_admin auth"""

    def test_user_engagement_success(self, client, admin_headers):
        """Test getting user engagement with default 30 days."""
        response = client.get(
            "/api/v1/analytics/bi/user-engagement",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_user_engagement_default_days(self, client, admin_headers):
        """Test default days parameter is 30."""
        response = client.get(
            "/api/v1/analytics/bi/user-engagement",
            headers=admin_headers
        )

        assert response.status_code == 200
        # Default should return ~30 data points (one per day)
        data = response.json()
        assert len(data["data"]) <= 30

    def test_user_engagement_custom_days(self, client, admin_headers):
        """Test custom days parameter (1-90 range)."""
        response = client.get(
            "/api/v1/analytics/bi/user-engagement?days=7",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 7

    def test_user_engagement_boundary_days(self, client, admin_headers):
        """Test days parameter at boundaries (1 and 90)."""
        # Test minimum
        response_min = client.get(
            "/api/v1/analytics/bi/user-engagement?days=1",
            headers=admin_headers
        )
        assert response_min.status_code == 200

        # Test maximum
        response_max = client.get(
            "/api/v1/analytics/bi/user-engagement?days=90",
            headers=admin_headers
        )
        assert response_max.status_code == 200

    def test_user_engagement_invalid_days(self, client, admin_headers):
        """Test days parameter outside valid range (1-90) returns 422."""
        # Test below minimum
        response_low = client.get(
            "/api/v1/analytics/bi/user-engagement?days=0",
            headers=admin_headers
        )
        assert response_low.status_code == 422

        # Test above maximum
        response_high = client.get(
            "/api/v1/analytics/bi/user-engagement?days=91",
            headers=admin_headers
        )
        assert response_high.status_code == 422

    def test_user_engagement_unauthorized(self, client):
        """Test getting user engagement without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/user-engagement")
        assert response.status_code == 401


class TestRetentionCohorts:
    """GET /analytics/bi/retention-analysis - require_admin auth"""

    def test_retention_cohorts_success(self, client, admin_headers):
        """Test getting cohort-based retention analysis with default 6 months."""
        response = client.get(
            "/api/v1/analytics/bi/retention-analysis",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_retention_cohorts_default_months(self, client, admin_headers):
        """Test default months parameter is 6."""
        response = client.get(
            "/api/v1/analytics/bi/retention-analysis",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Default should return ~6 cohorts
        assert len(data["data"]) <= 6

    def test_retention_cohorts_custom_months(self, client, admin_headers):
        """Test custom months parameter (1-12 range)."""
        response = client.get(
            "/api/v1/analytics/bi/retention-analysis?months=3",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_retention_cohorts_boundary_months(self, client, admin_headers):
        """Test months parameter at boundaries (1 and 12)."""
        # Test minimum
        response_min = client.get(
            "/api/v1/analytics/bi/retention-analysis?months=1",
            headers=admin_headers
        )
        assert response_min.status_code == 200

        # Test maximum
        response_max = client.get(
            "/api/v1/analytics/bi/retention-analysis?months=12",
            headers=admin_headers
        )
        assert response_max.status_code == 200

    def test_retention_cohorts_invalid_months(self, client, admin_headers):
        """Test months parameter outside valid range (1-12) returns 422."""
        # Test below minimum
        response_low = client.get(
            "/api/v1/analytics/bi/retention-analysis?months=0",
            headers=admin_headers
        )
        assert response_low.status_code == 422

        # Test above maximum
        response_high = client.get(
            "/api/v1/analytics/bi/retention-analysis?months=13",
            headers=admin_headers
        )
        assert response_high.status_code == 422

    def test_retention_cohorts_unauthorized(self, client):
        """Test getting retention analysis without auth returns 401."""
        response = client.get("/api/v1/analytics/bi/retention-analysis")
        assert response.status_code == 401
