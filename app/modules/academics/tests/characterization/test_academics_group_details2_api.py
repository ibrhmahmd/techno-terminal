"""Characterization tests for the Academics Group Details HTTP API (ticket #18, Part 3 of 3).

Pins the exact status codes, response envelopes and field shapes of 2 endpoints
served by ``app/modules/academics/api/group_details_router.py`` BEFORE the Academics
HTTP layer moves into ``app/modules/academics/api/``:

    GET /finance/groups/{group_id}/payments
    GET /academics/groups/{group_id}/enrollments/all

Buckets
-------
* Both services open their own ``get_session()``; rows created via the rollback-only
  ``uow`` fixture are invisible to them. Tests therefore seed data through the
  committed ``db_session`` fixture with uuid-tagged values.
* Both endpoints are read-only (no writes), so no cleanup is needed.
* No Supabase/Twilio/Gmail dependencies — academics endpoints do not need them.

Pinned quirks (not endorsed)
----------------------------
* An unknown group id is NOT a 404 on either endpoint: both return 200 with empty
  ``by_level`` / ``grouped_by_level`` and zero summaries.
* ``transfer_options`` is a GLOBAL list of every active group (excluding the
  requested one), so its length is not deterministic across a shared DB; tests look
  up the group they created by id.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/academics/tests/characterization/test_academics_group_details2_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import datetime, timezone

from app.modules.finance.models.payment import Payment
from app.modules.finance.models.receipt import Receipt
from app.testing.db_helpers import (
    create_student_with_enrollment,
    create_test_course,
    create_test_group,
    create_test_group_level,
)


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_receipt(db_session, payment_method: str = "cash", receipt_number: str = None) -> Receipt:
    """Insert a committed receipt.

    ``tests.utils.db_helpers.create_test_receipt`` uses a naive ``utcnow()`` which the
    timezone-aware ``timestamptz`` columns reject, so build it with an aware datetime.
    """
    receipt = Receipt(
        payer_name="Test Payer",
        payment_method=payment_method,
        receipt_number=receipt_number,
        paid_at=datetime.now(timezone.utc),
    )
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    return receipt


def _make_payment(
    db_session, receipt_id: int, student_id: int, amount: float,
    enrollment_id: int, transaction_type: str = "payment",
) -> Payment:
    """Insert a committed payment (aware datetime to satisfy the timestamptz column)."""
    payment = Payment(
        receipt_id=receipt_id,
        student_id=student_id,
        enrollment_id=enrollment_id,
        amount=amount,
        transaction_type=transaction_type,
        payment_type="course_level",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


_PAYMENT_IN_LEVEL_FIELDS = {
    "payment_id",
    "student_id",
    "student_name",
    "amount",
    "discount_amount",
    "payment_date",
    "payment_method",
    "status",
    "receipt_number",
    "receipt_id",
    "transaction_type",
}

_LEVEL_PAYMENT_SUMMARY_FIELDS = {
    "level_number",
    "level_status",
    "course_name",
    "expected",
    "collected",
    "due",
    "total_students",
    "paid_count",
    "unpaid_count",
    "payments",
}

_ENROLLMENT_IN_LEVEL_FIELDS = {
    "enrollment_id",
    "student_id",
    "status",
    "enrolled_at",
    "dropped_at",
    "sessions_attended",
    "sessions_total",
    "payment_status",
    "amount_due",
    "amount_paid",
    "discount_applied",
    "can_transfer",
    "can_drop",
}


# ── GET /api/v1/finance/groups/{group_id}/payments ─────────────────────────────


def test_get_group_payments_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET payments returns the envelope, aggregate summary and per-level payment DTO."""
    course = create_test_course(db_session, name=f"Pay Course {_short()}")
    group = create_test_group(db_session, course_id=course.id, level_number=1)
    create_test_group_level(db_session, group_id=group.id, level_number=1, course_id=course.id)
    _, student, enrollment = create_student_with_enrollment(
        db_session, group_id=group.id, level_number=1, amount_due=500.0,
    )
    receipt = _make_receipt(db_session, payment_method="cash", receipt_number=f"R-{_short()}")
    _make_payment(
        db_session, receipt_id=receipt.id, student_id=student.id, amount=200.0,
        enrollment_id=enrollment.id, transaction_type="payment",
    )

    r = client_with_uow.get(
        f"/api/v1/finance/groups/{group.id}/payments",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Group payments loaded successfully."
    data = body["data"]
    assert set(data) == {"group_id", "generated_at", "cache_ttl", "summary", "by_level"}
    assert data["group_id"] == group.id
    assert data["cache_ttl"] == 300
    assert set(data["summary"]) == {
        "total_expected_all_levels",
        "total_collected_all_levels",
        "total_due_all_levels",
        "collection_rate",
    }
    assert data["summary"]["total_expected_all_levels"] == 500.0
    assert data["summary"]["total_collected_all_levels"] == 200.0
    assert data["summary"]["total_due_all_levels"] == 300.0
    assert data["summary"]["collection_rate"] == 0.4

    assert len(data["by_level"]) == 1
    level = data["by_level"][0]
    assert set(level) == _LEVEL_PAYMENT_SUMMARY_FIELDS
    assert level["level_number"] == 1
    assert level["level_status"] == "active"
    assert level["course_name"] == course.name
    assert level["expected"] == 500.0
    assert level["collected"] == 200.0
    assert level["due"] == 300.0
    assert level["total_students"] == 1
    assert level["paid_count"] == 1
    assert level["unpaid_count"] == 0

    assert len(level["payments"]) == 1
    payment = level["payments"][0]
    assert set(payment) == _PAYMENT_IN_LEVEL_FIELDS
    assert payment["student_id"] == student.id
    assert payment["student_name"] == student.full_name
    assert payment["amount"] == 200.0
    assert payment["discount_amount"] == 0.0
    assert isinstance(payment["payment_date"], str) and len(payment["payment_date"]) == 10
    assert payment["payment_method"] == "cash"
    assert payment["status"] == "completed"
    assert payment["receipt_number"] == receipt.receipt_number
    # Pinned quirk (suspected product bug): the repository selects p.receipt_id but
    # never puts it in the result dict, so receipt_id is always None in the response.
    assert payment["receipt_id"] is None
    assert payment["transaction_type"] == "payment"


def test_get_group_payments_unknown_group_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET payments for a nonexistent group returns 200 with empty by_level — no 404."""
    r = client_with_uow.get(
        "/api/v1/finance/groups/999999999/payments",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Group payments loaded successfully."
    data = body["data"]
    assert data["group_id"] == 999999999
    assert data["by_level"] == []
    assert data["summary"]["total_expected_all_levels"] == 0.0
    assert data["summary"]["total_collected_all_levels"] == 0.0
    assert data["summary"]["total_due_all_levels"] == 0.0
    assert data["summary"]["collection_rate"] == 0.0


def test_get_group_payments_invalid_group_is_422(client_with_uow, override_auth, mock_admin_headers):
    """GET payments with group_id < 1 fails path validation with 422."""
    r = client_with_uow.get(
        "/api/v1/finance/groups/0/payments",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_get_group_payments_requires_auth(client):
    """GET payments without auth returns 401."""
    r = client.get("/api/v1/finance/groups/1/payments")

    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False


# ── GET /api/v1/academics/groups/{group_id}/enrollments/all ────────────────────


def test_get_group_enrollments_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET enrollments returns the student lookup, per-level enrollment DTOs and transfer options."""
    course = create_test_course(db_session, name=f"Enr Course {_short()}")
    group = create_test_group(db_session, course_id=course.id, level_number=1)
    create_test_group_level(db_session, group_id=group.id, level_number=1, course_id=course.id)
    _, student, enrollment = create_student_with_enrollment(
        db_session, group_id=group.id, level_number=1, amount_due=500.0,
    )
    transfer_group = create_test_group(db_session, course_id=course.id, max_capacity=7)

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/enrollments/all",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Group enrollments loaded successfully."
    data = body["data"]
    assert set(data) == {
        "group_id",
        "generated_at",
        "cache_ttl",
        "students",
        "grouped_by_level",
        "transfer_options",
    }
    assert data["group_id"] == group.id
    assert data["cache_ttl"] == 300

    lookup = data["students"][str(student.id)]
    assert set(lookup) == {"student_id", "student_name", "phone", "parent_name"}
    assert lookup["student_id"] == student.id
    assert lookup["student_name"] == student.full_name
    assert lookup["parent_name"] is not None

    assert len(data["grouped_by_level"]) == 1
    level = data["grouped_by_level"][0]
    assert set(level) == {"level_number", "level_status", "course_name", "enrollments", "summary"}
    assert level["level_number"] == 1
    assert level["level_status"] == "active"
    assert level["course_name"] == course.name
    assert set(level["summary"]) == {"total", "active", "completed", "dropped", "paid", "unpaid"}
    assert level["summary"] == {
        "total": 1,
        "active": 1,
        "completed": 0,
        "dropped": 0,
        "paid": 0,
        "unpaid": 1,
    }

    assert len(level["enrollments"]) == 1
    enr = level["enrollments"][0]
    assert set(enr) == _ENROLLMENT_IN_LEVEL_FIELDS
    assert enr["enrollment_id"] == enrollment.id
    assert enr["student_id"] == student.id
    assert enr["status"] == "active"
    assert enr["dropped_at"] is None
    assert enr["sessions_attended"] == 0
    assert enr["sessions_total"] == 0
    assert enr["payment_status"] == "due"
    assert enr["amount_due"] == 500.0
    assert enr["amount_paid"] == 0.0
    assert enr["discount_applied"] == 0.0
    assert enr["can_transfer"] is True
    assert enr["can_drop"] is True

    transfer = {t["group_id"]: t for t in data["transfer_options"]}[transfer_group.id]
    assert set(transfer) == {"group_id", "group_name", "course_name", "available_slots"}
    assert transfer["group_name"] == transfer_group.name
    assert transfer["course_name"] == course.name
    assert transfer["available_slots"] == 7


def test_get_group_enrollments_unknown_group_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET enrollments for a nonexistent group returns 200 with empty level groups — no 404."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/enrollments/all",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Group enrollments loaded successfully."
    data = body["data"]
    assert data["group_id"] == 999999999
    assert data["students"] == {}
    assert data["grouped_by_level"] == []
    assert isinstance(data["transfer_options"], list)


def test_get_group_enrollments_invalid_group_is_422(client_with_uow, override_auth, mock_admin_headers):
    """GET enrollments with group_id < 1 fails path validation with 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/0/enrollments/all",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_get_group_enrollments_requires_auth(client):
    """GET enrollments without auth returns 401."""
    r = client.get("/api/v1/academics/groups/1/enrollments/all")

    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
