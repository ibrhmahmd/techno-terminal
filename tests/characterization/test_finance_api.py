"""Characterization tests for the Finance HTTP API (ticket #22).

Pins status codes, envelopes and field shapes of the finance endpoints served by
``app/modules/finance/api/``
BEFORE the HTTP layer moves into ``app/modules/finance/api/``:

    POST /finance/receipts, POST /finance/refunds, GET /finance/competition-fees,
    POST /finance/risk/overpayment, GET /students/{id}/balance,
    GET /balance/unpaid-enrollments, GET /finance/payments/{id},
    POST /finance/payments/{id}/send-receipt,
    GET /finance/receipts/{id}, GET /finance/receipts, GET /finance/receipts/{id}/pdf,
    GET /finance/receipts/{id}/generate, POST /finance/receipts/batch-generate,
    GET /finance/reports/daily-collections, GET /finance/reports/daily-receipts

(The competition fee routes and ``GET /crm/students/{id}/payments`` are pinned in
the competitions and crm characterization files.)

Buckets
-------
* Finance services use the request ``get_db`` session / ``FinanceUnitOfWork`` and
  really commit. Every test seeds committed, uuid-tagged rows through ``db_session``
  and reaches receipts/payments by creating them through the API.
* Receipt creation can schedule notifications, so ``get_notification_service`` is
  replaced by a no-op (``noop_notifications``); no real mail/SMS can be sent.

Pinned quirks (pinned, not endorsed)
------------------------------------
See the tests marked "current behaviour".
"""

import uuid
from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment


class _Noop:
    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return None


@pytest.fixture
def noop_notifications(app):
    from app.modules.notifications.api.deps import get_notification_service

    svc = _Noop()
    app.dependency_overrides[get_notification_service] = lambda: svc
    try:
        yield svc
    finally:
        app.dependency_overrides.pop(get_notification_service, None)


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _seed_enrollment(db_session, amount_due: float = 1000.0):
    course = Course(
        name=f"FinCourse {_short()}", category="software", price_per_level=amount_due,
        sessions_per_level=8, is_active=True,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    group = Group(
        name=f"FinGroup {_short()}", course_id=course.id, level_number=1, max_capacity=15,
        default_day="Saturday", default_time_start=time(14, 0), default_time_end=time(16, 0),
        status="active",
    )
    db_session.add(group)
    # inactive on purpose: committed test rows must not pile up in the "active" bucket that
    # legacy list tests page through (limit 200)
    student = Student(full_name=f"Fin Student {_short()}", phone=f"555{_short()[:7]}", status="inactive")
    db_session.add(student)
    db_session.commit()
    db_session.refresh(group)
    db_session.refresh(student)
    enrollment = Enrollment(
        student_id=student.id, group_id=group.id, level_number=1, amount_due=amount_due,
        discount_applied=0.0, status="active", enrolled_at=date(2026, 1, 5),
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)
    return course, group, student, enrollment


def _create_receipt(client, headers, student, enrollment, amount=400.0, payer="Parent X", **extra):
    body = {
        "payer_name": payer,
        "method": "cash",
        "lines": [{
            "student_id": student.id, "enrollment_id": enrollment.id,
            "amount": amount, "payment_type": "course_level",
        }],
    }
    body.update(extra)
    return client.post("/api/v1/finance/receipts", headers=headers, json=body)


# ── POST /finance/receipts ────────────────────────────────────────────────────


def test_create_receipt(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)

    r = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment)

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Receipt created successfully."
    data = body["data"]
    assert set(data) == {
        "receipt_id", "receipt_number", "payment_method", "paid_at", "lines", "total", "payment_ids",
    }
    assert data["payment_method"] == "cash"
    assert data["lines"] == 1
    assert data["total"] == 400.0
    assert len(data["payment_ids"]) == 1
    # current behaviour (pinned, not endorsed): the creation response carries an empty
    # receipt_number; the number is only visible when the receipt is read back.
    assert data["receipt_number"] == ""
    detail = client_with_uow.get(f"/api/v1/finance/receipts/{data['receipt_id']}", headers=mock_admin_headers).json()["data"]
    assert detail["receipt"]["receipt_number"].startswith("R-")


def test_create_receipt_normalizes_method_label(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)

    r = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, method="bolt")

    assert r.status_code == 201
    assert r.json()["data"]["payment_method"] == "instapay"


def test_create_receipt_validation(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    empty = client_with_uow.post("/api/v1/finance/receipts", headers=h, json={"lines": []})
    assert empty.status_code == 409
    assert empty.json()["message"] == "Receipt must have at least one line item."
    assert client_with_uow.post(
        "/api/v1/finance/receipts", headers=h,
        json={"lines": [{"student_id": 1, "amount": 0}]},
    ).status_code == 422
    assert client_with_uow.post(
        "/api/v1/finance/receipts", headers=h,
        json={"method": "barter", "lines": [{"student_id": 1, "amount": 5}]},
    ).status_code == 422


def test_create_receipt_overpayment_check_crashes_with_500(
    app, client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """current behaviour (pinned, not endorsed): with allow_credit=false the overpayment check
    builds ``OverpaymentRiskItem(amount=...)``, a keyword the item does not accept, so the
    request fails with 500 instead of the intended business-rule error."""
    _, _, student, enrollment = _seed_enrollment(db_session, amount_due=100.0)

    r = TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/finance/receipts", headers=mock_admin_headers,
        json={"allow_credit": False, "lines": [
            {"student_id": student.id, "enrollment_id": enrollment.id, "amount": 500.0}]},
    )

    assert r.status_code == 500


# ── POST /finance/refunds ─────────────────────────────────────────────────────


def test_issue_refund(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    payment_id = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=400.0).json()["data"]["payment_ids"][0]

    r = client_with_uow.post(
        "/api/v1/finance/refunds", headers=mock_admin_headers,
        json={"payment_id": payment_id, "amount": 100.0, "reason": "test refund"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Refund issued successfully."
    assert set(body["data"]) == {"receipt_number", "refunded_amount", "new_balance"}
    assert body["data"]["refunded_amount"] == 100.0


def test_issue_refund_more_than_paid(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    payment_id = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=50.0).json()["data"]["payment_ids"][0]

    r = client_with_uow.post(
        "/api/v1/finance/refunds", headers=mock_admin_headers,
        json={"payment_id": payment_id, "amount": 500.0, "reason": "too much"},
    )

    assert r.status_code == 409
    assert r.json()["success"] is False


def test_issue_refund_unknown_payment(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post(
        "/api/v1/finance/refunds", headers=mock_admin_headers,
        json={"payment_id": 999999999, "amount": 10.0, "reason": "x"},
    )
    assert r.status_code == 404
    assert r.json()["success"] is False


# ── GET /finance/competition-fees ─────────────────────────────────────────────


def test_unpaid_competition_fees_empty_for_student_without_teams(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, _, student, _ = _seed_enrollment(db_session)

    r = client_with_uow.get(f"/api/v1/finance/competition-fees?student_id={student.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == []


def test_unpaid_competition_fees_requires_student_id(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.get("/api/v1/finance/competition-fees", headers=mock_admin_headers).status_code == 422


# ── POST /finance/risk/overpayment ────────────────────────────────────────────


def test_overpayment_risk_always_crashes_with_500(
    app, client_with_uow, override_auth, mock_admin_headers, db_session
):
    """current behaviour (pinned, not endorsed): the request model ``ReceiptLineRequest`` has no
    ``team_member_id`` but the endpoint reads it, so every call fails with 500."""
    _, _, student, enrollment = _seed_enrollment(db_session, amount_due=100.0)

    r = TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/finance/risk/overpayment", headers=mock_admin_headers,
        json={"lines": [{"student_id": student.id, "enrollment_id": enrollment.id, "amount": 300.0}]},
    )

    assert r.status_code == 500


def test_overpayment_risk_validation(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.post(
        "/api/v1/finance/risk/overpayment", headers=mock_admin_headers, json={}
    ).status_code == 422


# ── GET /students/{id}/balance ────────────────────────────────────────────────


def test_student_balance(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session, amount_due=1000.0)
    _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=400.0)

    r = client_with_uow.get(f"/api/v1/students/{student.id}/balance", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {
        "student_id", "total_amount_due", "total_discounts", "total_paid", "net_balance",
        "enrollment_count", "unpaid_enrollments", "enrollments",
    }
    assert data["total_amount_due"] == 1000.0
    assert data["total_paid"] == 400.0
    assert data["net_balance"] == -600.0
    assert data["enrollment_count"] == 1
    assert data["unpaid_enrollments"] == 1
    e = data["enrollments"][0]
    assert set(e) == {
        "enrollment_id", "student_id", "group_id", "level_number", "amount_due", "discount_applied",
        "total_paid", "total_refunded", "remaining_balance", "status", "is_paid",
    }
    assert e["remaining_balance"] == -600.0
    assert e["is_paid"] is False


def test_student_balance_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): unknown student -> 200 with an all-zero summary."""
    r = client_with_uow.get("/api/v1/students/999999999/balance", headers=mock_admin_headers)
    assert r.status_code == 200
    assert r.json()["data"] == {
        "student_id": 999999999, "total_amount_due": 0.0, "total_discounts": 0.0, "total_paid": 0.0,
        "net_balance": 0.0, "enrollment_count": 0, "unpaid_enrollments": 0, "enrollments": [],
    }


# ── GET /balance/unpaid-enrollments ───────────────────────────────────────────


def test_unpaid_enrollments_lists_debt(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, group, student, enrollment = _seed_enrollment(db_session, amount_due=700.0)

    r = client_with_uow.get(f"/api/v1/balance/unpaid-enrollments?group_id={group.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"success", "data", "total", "skip", "limit"}
    assert body["total"] == 1
    item = body["data"][0]
    assert set(item) == {
        "enrollment_id", "student_id", "student_name", "group_id", "group_name", "course_name",
        "level_number", "amount_due", "discount_applied", "total_paid", "remaining_balance", "enrolled_at",
    }
    assert item["enrollment_id"] == enrollment.id
    # current behaviour (pinned, not endorsed): debt is reported as a POSITIVE remaining_balance
    # here, while GET /students/{id}/balance reports the same debt as negative.
    assert item["remaining_balance"] == 700.0


def test_unpaid_enrollments_pagination_validation(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.get("/api/v1/balance/unpaid-enrollments?limit=0", headers=mock_admin_headers).status_code == 422
    assert client_with_uow.get("/api/v1/balance/unpaid-enrollments?skip=-1", headers=mock_admin_headers).status_code == 422


# ── GET /finance/payments/{id} / send-receipt ─────────────────────────────────


def test_payment_details(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, group, student, enrollment = _seed_enrollment(db_session)
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=250.0).json()["data"]

    r = client_with_uow.get(f"/api/v1/finance/payments/{created['payment_ids'][0]}", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {
        "id", "student_id", "amount", "payment_type", "transaction_type", "discount_amount", "notes",
        "created_at", "receipt", "enrollment", "student", "parent",
    }
    assert data["id"] == created["payment_ids"][0]
    assert data["student_id"] == student.id
    assert float(data["amount"]) == 250.0
    assert data["receipt"]["receipt_id"] == created["receipt_id"]
    assert data["enrollment"]["enrollment_id"] == enrollment.id
    assert data["enrollment"]["group_id"] == group.id
    assert data["student"]["full_name"] == student.full_name


def test_payment_details_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/finance/payments/999999999", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["success"] is False


def test_send_receipt_unknown_payment_is_404(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    r = client_with_uow.post(
        "/api/v1/finance/payments/999999999/send-receipt", headers=mock_admin_headers, json={"method": "email"},
    )
    assert r.status_code == 404


def test_send_receipt_without_parent_is_200_with_failure_payload(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """current behaviour (pinned, not endorsed): a student with no parent is a 200 whose payload
    says success=false (the envelope still says success=true)."""
    _, _, student, enrollment = _seed_enrollment(db_session)
    payment_id = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=100.0).json()["data"]["payment_ids"][0]

    r = client_with_uow.post(
        f"/api/v1/finance/payments/{payment_id}/send-receipt", headers=mock_admin_headers, json={"method": "email"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == f"No parent found for student {student.full_name}."
    assert body["data"]["success"] is False
    assert body["data"]["recipient_contact"] is None
    assert set(body["data"]) == {"success", "message", "receipt_id", "recipient_contact", "sent_at"}


def test_send_receipt_invalid_method_crashes_with_500(
    app, client_with_uow, override_auth, mock_admin_headers, noop_notifications
):
    """current behaviour (pinned, not endorsed): the method validator's ValueError cannot be
    JSON-serialised by the 422 handler (same pattern as the attendance duplicate-id bug), so
    the response is 500."""
    r = TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/finance/payments/1/send-receipt", headers=mock_admin_headers, json={"method": "carrier"},
    )
    assert r.status_code == 500


# ── Receipts: GET /finance/receipts/{id}, search, pdf, generate, batch ────────


def test_get_receipt_detail(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=300.0).json()["data"]

    r = client_with_uow.get(f"/api/v1/finance/receipts/{created['receipt_id']}", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"receipt", "lines", "total"}
    assert set(data["receipt"]) == {"id", "receipt_number", "payer_name", "payment_method", "paid_at", "notes"}
    assert data["receipt"]["id"] == created["receipt_id"]
    assert data["total"] == 300.0
    assert len(data["lines"]) == 1
    assert set(data["lines"][0]) == {
        "id", "student_id", "enrollment_id", "amount", "transaction_type", "payment_type", "discount", "notes",
    }


def test_get_receipt_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/finance/receipts/999999999", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["message"] == "Receipt not found"


def test_search_receipts(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    payer = f"Payer {_short()}"
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=120.0, payer=payer).json()["data"]
    today = date.today().isoformat()

    r = client_with_uow.get(
        f"/api/v1/finance/receipts?from_date={today}&to_date={today}&payer_name={payer}",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert [x["id"] for x in data] == [created["receipt_id"]]
    assert set(data[0]) == {"id", "receipt_number", "payer_name", "payment_method", "paid_at"}


def test_search_receipts_range_too_large(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get(
        "/api/v1/finance/receipts?from_date=2025-01-01&to_date=2026-01-01", headers=mock_admin_headers
    )
    assert r.status_code == 422
    assert "Date range too large" in r.json()["message"]


def test_receipt_pdf(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=80.0).json()["data"]

    r = client_with_uow.get(f"/api/v1/finance/receipts/{created['receipt_id']}/pdf", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert "attachment; filename=\"receipt_" in r.headers["content-disposition"]


def test_receipt_pdf_not_found(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/finance/receipts/999999999/pdf", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["message"] == "Receipt not found"


def test_generate_receipt_json_and_text(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=60.0).json()["data"]

    j = client_with_uow.get(f"/api/v1/finance/receipts/{created['receipt_id']}/generate", headers=mock_admin_headers)
    t = client_with_uow.get(
        f"/api/v1/finance/receipts/{created['receipt_id']}/generate?as_text=true", headers=mock_admin_headers
    )

    assert j.status_code == 200
    data = j.json()["data"]
    assert set(data) == {"content", "content_type"}
    assert data["content_type"] == "text/plain"
    assert data["content"].startswith("=" * 10)
    assert "RECEIPT #: R-" in data["content"]
    assert t.status_code == 200
    assert t.headers["content-type"].startswith("text/plain")
    assert "RECEIPT #: R-" in t.text


def test_batch_generate_receipts(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=60.0).json()["data"]

    r = client_with_uow.post(
        "/api/v1/finance/receipts/batch-generate", headers=mock_admin_headers,
        json={"receipt_ids": [created["receipt_id"], 999999999]},
    )

    assert r.status_code == 200
    items = r.json()["data"]
    assert [i["receipt_id"] for i in items] == [created["receipt_id"], 999999999]
    assert items[0]["success"] is True
    assert items[1]["success"] is False
    assert set(items[0]) == {"receipt_id", "success", "content", "error_message", "error_code"}


# ── Reports ───────────────────────────────────────────────────────────────────


def test_daily_collections_and_receipts(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    _, _, student, enrollment = _seed_enrollment(db_session)
    created = _create_receipt(client_with_uow, mock_admin_headers, student, enrollment, amount=55.0).json()["data"]

    col = client_with_uow.get("/api/v1/finance/reports/daily-collections", headers=mock_admin_headers)
    rec = client_with_uow.get("/api/v1/finance/reports/daily-receipts", headers=mock_admin_headers)

    assert col.status_code == 200
    assert col.json()["success"] is True
    cash = [c for c in col.json()["data"] if c["payment_method"] == "cash"]
    assert len(cash) == 1
    assert set(cash[0]) == {"payment_method", "total_amount", "receipt_count", "target_date"}
    assert cash[0]["target_date"] == date.today().isoformat()
    assert rec.status_code == 200
    mine = [x for x in rec.json()["data"] if x["receipt_id"] == created["receipt_id"]]
    assert len(mine) == 1
    assert set(mine[0]) == {"receipt_id", "receipt_number", "payer_name", "total_amount", "payment_method", "issued_at"}
    assert mine[0]["total_amount"] == 55.0


def test_daily_reports_accept_target_date(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.get(
        "/api/v1/finance/reports/daily-collections?target_date=2020-01-01", headers=mock_admin_headers
    ).json()["data"] == []
    assert client_with_uow.get(
        "/api/v1/finance/reports/daily-receipts?target_date=2020-01-01", headers=mock_admin_headers
    ).json()["data"] == []


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_finance_endpoints_require_auth(client):
    assert client.post("/api/v1/finance/receipts", json={}).status_code == 401
    assert client.post("/api/v1/finance/refunds", json={}).status_code == 401
    assert client.get("/api/v1/finance/competition-fees?student_id=1").status_code == 401
    assert client.post("/api/v1/finance/risk/overpayment", json={"lines": []}).status_code == 401
    assert client.get("/api/v1/students/1/balance").status_code == 401
    assert client.get("/api/v1/balance/unpaid-enrollments").status_code == 401
    assert client.get("/api/v1/finance/payments/1").status_code == 401
    assert client.post("/api/v1/finance/payments/1/send-receipt", json={"method": "email"}).status_code == 401
    assert client.get("/api/v1/finance/receipts/1").status_code == 401
    assert client.get("/api/v1/finance/receipts?from_date=2026-01-01&to_date=2026-01-02").status_code == 401
    assert client.get("/api/v1/finance/receipts/1/pdf").status_code == 401
    assert client.get("/api/v1/finance/receipts/1/generate").status_code == 401
    assert client.post("/api/v1/finance/receipts/batch-generate", json={"receipt_ids": []}).status_code == 401
    assert client.get("/api/v1/finance/reports/daily-collections").status_code == 401
    assert client.get("/api/v1/finance/reports/daily-receipts").status_code == 401
