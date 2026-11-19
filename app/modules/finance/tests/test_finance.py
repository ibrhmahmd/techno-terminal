"""
app/modules/finance/tests/test_finance.py
──────────────────────
Phase 5: Finance Endpoints Testing

Covers:
- POST /finance/receipts (create receipt)
- GET /finance/receipts/{id} (get receipt)
- GET /finance/receipts (search receipts)
- POST /finance/refunds (issue refund)
- GET /finance/competition-fees?student_id= (get unpaid fees)
- POST /finance/risk/overpayment (overpayment risk)
- GET /finance/receipts/{id}/pdf (download PDF)

All tests verify:
- Authentication requirements (401 vs 200/201)
- Authorization (admin only for writes)
- Response schema compliance (ApiResponse envelope)
"""
import pytest
from datetime import date, timedelta
from app.shared.datetime_utils import cairo_today


class TestReceiptsRead:
    """Tests for reading receipt data."""
    
    def test_get_receipt_success(self, client, mock_admin_headers, override_auth, db_session):
        """
        GET /finance/receipts/{id} returns receipt details.
        Requires authentication (any role).
        """
        from app.testing.db_helpers import create_test_receipt

        receipt = create_test_receipt(db_session)
        response = client.get(
            f"/api/v1/finance/receipts/{receipt.id}",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["receipt"]["id"] == receipt.id
    
    def test_get_receipt_not_found(self, client, mock_admin_headers, override_auth):
        """
        GET /finance/receipts/{id} for non-existent ID returns 404.
        """
        response = client.get(
            "/api/v1/finance/receipts/99999",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestReceiptsSearch:
    """Tests for searching receipts."""
    
    def test_search_receipts_success(self, client, mock_admin_headers, override_auth):
        today = cairo_today()
        response = client.get(
            f"/api/v1/finance/receipts?from_date={today - timedelta(days=30)}&to_date={today}",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    def test_search_receipts_range_too_large(self, client, mock_admin_headers, override_auth):
        """A date range over 90 days returns 422."""
        today = cairo_today()
        response = client.get(
            f"/api/v1/finance/receipts?from_date={today - timedelta(days=200)}&to_date={today}",
            headers=mock_admin_headers
        )
        assert response.status_code == 422
        assert response.json()["error"] == "ValidationError"
    
    def test_search_receipts_missing_dates(self, client, mock_admin_headers, override_auth):
        """
        GET /finance/receipts without required dates returns 422.
        """
        response = client.get(
            "/api/v1/finance/receipts",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "ValidationError"


class TestReceiptsCreate:
    """Tests for creating receipts."""
    
    def test_create_receipt_validation_error(self, client, mock_admin_headers, override_auth):
        """
        POST /finance/receipts with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=mock_admin_headers,
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
    
    def test_issue_refund_validation_error(self, client, mock_admin_headers, override_auth):
        """
        POST /finance/refunds with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/finance/refunds",
            headers=mock_admin_headers,
            json={
                "payment_id": "not-an-integer",  # Invalid type
                "amount": 50.0
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestCompetitionFees:
    """Tests for competition fee endpoints."""
    
    def test_get_unpaid_competition_fees(self, client, mock_admin_headers, override_auth, db_session):
        from app.testing.db_helpers import create_test_student

        student = create_test_student(db_session)
        db_session.commit()
        response = client.get(
            f"/api/v1/finance/competition-fees?student_id={student.id}",
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        assert response.json()["data"] == []


class TestRiskPreview:
    """Tests for overpayment risk preview."""
    
    def test_preview_risk_validation_error(self, client, mock_admin_headers, override_auth):
        response = client.post(
            "/api/v1/finance/risk/overpayment",
            headers=mock_admin_headers,
            json={
                "lines": "not-a-list"
            }
        )
        
        assert response.status_code == 422
        assert response.json()["error"] == "ValidationError"


class TestFinanceAuth:
    """Tests for authentication and authorization."""
    
    def test_get_receipt_requires_auth(self, client):
        """
        GET /finance/receipts/{id} without auth returns 401.
        """
        response = client.get("/api/v1/finance/receipts/1")
        assert response.status_code == 401
    
    def test_create_receipt_requires_admin(self, client, mock_admin_headers, override_auth):
        """
        POST /finance/receipts requires admin role.
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=mock_admin_headers,
            json={"payer_name": "Test"}
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
    
    def test_search_receipts_requires_admin(self, client, mock_admin_headers, override_auth):
        """
        GET /finance/receipts requires admin role.
        """
        today = cairo_today().isoformat()
        response = client.get(
            f"/api/v1/finance/receipts?from_date=2024-01-01&to_date={today}",
            headers=mock_admin_headers
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401


class TestPaymentMethodNormalization:
    """
    Tests for payment method normalization (Feature 029).

    Verifies that the @field_validator on CreateReceiptRequest normalizes
    all frontend input formats (icon names, display labels, lowercase labels)
    to canonical backend values.
    """

    # ── Direct DTO tests ─────────────────────────────────────────────────

    def test_cash_normalization(self):
        """Cash input variants all normalize to 'cash'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "cash"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "cash", f"{variant!r} should normalize to 'cash', got {dto.method!r}"

    def test_card_normalization(self):
        """Card input variants all normalize to 'card'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "card"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "card", f"{variant!r} should normalize to 'card', got {dto.method!r}"

    def test_transfer_normalization(self):
        """Transfer input variants all normalize to 'transfer'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "transfer"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "transfer", f"{variant!r} should normalize to 'transfer', got {dto.method!r}"

    def test_online_normalization(self):
        """Online input variants all normalize to 'online'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "online"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "online", f"{variant!r} should normalize to 'online', got {dto.method!r}"

    def test_ewallet_normalization(self):
        """E-Wallet input variants all normalize to 'ewallet'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "ewallet"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "ewallet", f"{variant!r} should normalize to 'ewallet', got {dto.method!r}"

    def test_instapay_normalization(self):
        """instaPay input variants all normalize to 'instapay'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "instapay"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "instapay", f"{variant!r} should normalize to 'instapay', got {dto.method!r}"

    def test_other_normalization(self):
        """Other input variants all normalize to 'other'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest
        from app.shared.constants import PAYMENT_METHOD_MAP

        for variant in [v for v in PAYMENT_METHOD_MAP if PAYMENT_METHOD_MAP[v] == "other"]:
            dto = CreateReceiptRequest(method=variant, lines=[])
            assert dto.method == "other", f"{variant!r} should normalize to 'other', got {dto.method!r}"

    def test_default_method_is_cash(self):
        """When method is omitted, default is 'cash'."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest

        dto_default = CreateReceiptRequest(lines=[])
        assert dto_default.method == "cash", f"Expected default 'cash', got {dto_default.method!r}"

        dto_explicit = CreateReceiptRequest(method="cash", lines=[])
        assert dto_explicit.method == "cash"

    def test_case_insensitive_normalization(self):
        """Casing variations are normalized via PAYMENT_METHOD_MAP lookup."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest

        dto_upper = CreateReceiptRequest(method="CASH", lines=[])
        assert dto_upper.method == "cash"

        dto_mixed = CreateReceiptRequest(method="E-Wallet", lines=[])
        assert dto_mixed.method == "ewallet"

        dto_lower = CreateReceiptRequest(method="instapay", lines=[])
        assert dto_lower.method == "instapay"

    def test_invalid_method_raises_validationerror(self):
        """Unrecognized values return a 422-style validation error."""
        from pydantic import ValidationError
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest

        with pytest.raises(ValidationError) as exc_info:
            CreateReceiptRequest(method="cryptocurrency", lines=[])
        error_msg = str(exc_info.value)
        # The error should mention the valid values
        assert "cash" in error_msg or "Input should be" in error_msg

    def test_invalid_method_typo_raises_validationerror(self):
        """Typo values (e.g., 'instapy') return 422."""
        from pydantic import ValidationError
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest

        with pytest.raises(ValidationError):
            CreateReceiptRequest(method="instapy", lines=[])

    def test_empty_method_string_invalid(self):
        """Empty string is not in the map and not a valid Literal value."""
        from pydantic import ValidationError
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest

        with pytest.raises(ValidationError):
            CreateReceiptRequest(method="", lines=[])

    def test_icon_name_mapping(self):
        """Material Icon names map to correct canonical values."""
        from app.modules.finance.api.schemas.receipt import CreateReceiptRequest

        dto = CreateReceiptRequest(method="payments", lines=[])
        assert dto.method == "cash"

        dto = CreateReceiptRequest(method="account_balance_wallet", lines=[])
        assert dto.method == "ewallet"

        dto = CreateReceiptRequest(method="bolt", lines=[])
        assert dto.method == "instapay"

        dto = CreateReceiptRequest(method="more_horiz", lines=[])
        assert dto.method == "other"

    # ── API-level tests ───────────────────────────────────────────────────

    def test_create_receipt_with_method_bolt(self, client, mock_admin_headers, override_auth):
        """
        POST /finance/receipts with method='bolt'.
        The validator should normalize 'bolt' → 'instapay'.
        Missing required 'lines' should get 422 (not a method validation error).
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=mock_admin_headers,
            json={"method": "bolt", "payer_name": "Test"}
        )
        assert response.status_code == 422  # missing lines, not method error
        data = response.json()
        assert data["success"] is False

    def test_create_receipt_with_invalid_method_returns_422(self, client, mock_admin_headers, override_auth):
        """
        POST /finance/receipts with an unrecognized method returns 422.
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=mock_admin_headers,
            json={"method": "cryptocurrency", "lines": []}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    def test_create_receipt_with_default_method(self, client, mock_admin_headers, override_auth):
        """
        POST /finance/receipts without method field defaults to 'cash'.
        Missing required 'lines' should get 422.
        """
        response = client.post(
            "/api/v1/finance/receipts",
            headers=mock_admin_headers,
            json={"payer_name": "Test"}
        )
        assert response.status_code == 422  # missing lines, not method error
        data = response.json()
        assert data["success"] is False


class TestCairoBusinessDay:
    """A receipt paid at 01:30 Cairo (22:30 UTC the day before) belongs to the Cairo day."""

    def test_late_utc_receipt_counts_on_the_cairo_day(self, uow):
        from datetime import datetime, timezone

        from app.modules.finance.repositories.receipt_repository import ReceiptRepository
        from app.modules.finance.repositories.reporting_repository import ReportingRepository
        from app.modules.finance.schemas import SearchReceiptsDTO
        from app.testing.db_helpers import create_test_payment, create_test_receipt, create_test_student

        session = uow.session
        receipts, reports = ReceiptRepository(session), ReportingRepository(session)
        day, prev = date(2026, 10, 14), date(2026, 10, 13)

        def ids(d):
            return {r.id for r in receipts.search(SearchReceiptsDTO(from_date=d, to_date=d))}

        def count(d):
            return sum(c.receipt_count for c in reports.get_daily_collections(d))

        before_day, before_prev = count(day), count(prev)
        student = create_test_student(session, status="inactive")
        receipt = create_test_receipt(session, paid_at=datetime(2026, 10, 13, 22, 30, tzinfo=timezone.utc))
        create_test_payment(session, receipt.id, student.id, 50.0)

        assert receipt.id in ids(day)
        assert receipt.id not in ids(prev)
        assert count(day) == before_day + 1
        assert count(prev) == before_prev
