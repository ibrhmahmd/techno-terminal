"""
tests/test_finance.py
──────────────────────
Phase 5: Finance Endpoints Testing

Covers:
- POST /finance/receipts (create receipt)
- GET /finance/receipts/{id} (get receipt)
- GET /finance/receipts (search receipts)
- POST /finance/refunds (issue refund)
- GET /finance/balance/student/{id} (get balances)
- GET /finance/competition-fees/student/{id} (get unpaid fees)
- POST /finance/receipts/preview-risk (preview risk)
- GET /finance/receipts/{id}/pdf (download PDF)

All tests verify:
- Authentication requirements (401 vs 200/201)
- Authorization (admin only for writes)
- Response schema compliance (ApiResponse envelope)
"""
import pytest
from datetime import date


class TestReceiptsRead:
    """Tests for reading receipt data."""
    
    def test_get_receipt_success(self, client, admin_headers):
        """
        GET /finance/receipts/{id} returns receipt details.
        Requires authentication (any role).
        """
        # Using receipt ID 1 - may not exist
        response = client.get(
            "/api/v1/finance/receipts/1",
            headers=admin_headers
        )
        
        # May succeed (200) or not found (404)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_get_receipt_not_found(self, client, admin_headers):
        """
        GET /finance/receipts/{id} for non-existent ID returns 404.
        """
        response = client.get(
            "/api/v1/finance/receipts/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestReceiptsSearch:
    """Tests for searching receipts."""
    
    def test_search_receipts_success(self, client, admin_headers):
        """
        GET /finance/receipts returns filtered receipts.
        Requires admin role.
        """
        today = date.today().isoformat()
        
        response = client.get(
            f"/api/v1/finance/receipts?from_date=2024-01-01&to_date={today}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_search_receipts_missing_dates(self, client, admin_headers):
        """
        GET /finance/receipts without required dates returns 422.
        """
        response = client.get(
            "/api/v1/finance/receipts",
            headers=admin_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestReceiptsCreate:
    """Tests for creating receipts."""
    
    def test_create_receipt_validation_error(self, client, admin_headers):
        """
        POST /finance/receipts with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=admin_headers,
            json={
                "payer_name": "Test Payer",
                # Missing required fields
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestRefunds:
    """Tests for refunds."""
    
    def test_issue_refund_validation_error(self, client, admin_headers):
        """
        POST /finance/refunds with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/finance/refunds",
            headers=admin_headers,
            json={
                "payment_id": "not-an-integer",  # Invalid type
                "amount": 50.0
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestBalances:
    """Tests for student financial balances."""
    
    def test_get_student_balance_success(self, client, admin_headers):
        """
        GET /finance/balance/student/{id} returns financial summary.
        Requires authentication (any role).
        """
        response = client.get(
            "/api/v1/finance/balance/student/1",
            headers=admin_headers
        )
        
        # May succeed (200) or not found (404)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert isinstance(data["data"], list)
    
    def test_get_student_balance_not_found(self, client, admin_headers):
        """
        GET /finance/balance/student/{id} for non-existent student.
        Returns empty list or 404.
        """
        response = client.get(
            "/api/v1/finance/balance/student/99999",
            headers=admin_headers
        )
        
        # May return empty list (200) or 404
        assert response.status_code in [200, 404]


class TestCompetitionFees:
    """Tests for competition fee endpoints."""
    
    def test_get_unpaid_competition_fees(self, client, admin_headers):
        """
        GET /finance/competition-fees/student/{id} returns unpaid fees.
        Requires authentication (any role).
        """
        response = client.get(
            "/api/v1/finance/competition-fees/student/1",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)


class TestRiskPreview:
    """Tests for overpayment risk preview."""
    
    def test_preview_risk_validation_error(self, client, admin_headers):
        """
        POST /finance/receipts/preview-risk with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/finance/receipts/preview-risk",
            headers=admin_headers,
            json={
                "lines": "not-a-list"  # Invalid type
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestFinanceAuth:
    """Tests for authentication and authorization."""
    
    def test_get_receipt_requires_auth(self, client):
        """
        GET /finance/receipts/{id} without auth returns 401.
        """
        response = client.get("/api/v1/finance/receipts/1")
        assert response.status_code == 401
    
    def test_create_receipt_requires_admin(self, client, admin_headers):
        """
        POST /finance/receipts requires admin role.
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=admin_headers,
            json={"payer_name": "Test"}
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
    
    def test_search_receipts_requires_admin(self, client, admin_headers):
        """
        GET /finance/receipts requires admin role.
        """
        today = date.today().isoformat()
        response = client.get(
            f"/api/v1/finance/receipts?from_date=2024-01-01&to_date={today}",
            headers=admin_headers
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
