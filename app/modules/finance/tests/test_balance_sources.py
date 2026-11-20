"""One source for balances and receipt totals: #255 (deleted payments), #254 (receipt
text vs API), #267 (group enrollment history). All tests use the rollback-only ``uow``."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text

from app.modules.academics.services.group_analytics_service import GroupAnalyticsService
from app.modules.finance.models import Payment, Receipt
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.modules.finance.services.receipt_generation_service import ReceiptGenerationService
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.notifications.repositories.reports_repository import ReportsRepository
from app.testing.db_helpers import (
    create_minimal_group_bundle,
    create_student_with_enrollment,
    create_test_enrollment,
)


def _receipt(session) -> Receipt:
    r = Receipt(
        payer_name="Payer",
        receipt_number=f"R-{uuid.uuid4().hex[:10]}",
        paid_at=datetime.now(timezone.utc),
    )
    session.add(r)
    session.flush()
    return r


def _line(session, receipt, student_id, enrollment_id, amount, kind="payment", **kw) -> Payment:
    p = Payment(
        receipt_id=receipt.id,
        student_id=student_id,
        enrollment_id=enrollment_id,
        amount=amount,
        transaction_type=kind,
        payment_type="course_level",
        **kw,
    )
    session.add(p)
    session.flush()
    return p


def _view(session, enrollment_id):
    return session.execute(
        text("select total_paid, amount_remaining from v_enrollment_balance where enrollment_id=:e"),
        {"e": enrollment_id},
    ).one()


def _student_with_enrollment(session, due):
    _, group, _, _ = create_minimal_group_bundle(session)
    _, student, enrollment = create_student_with_enrollment(session, group.id, amount_due=due)
    return student, enrollment, group.id


# ── #255 ──────────────────────────────────────────────────────────────────────

def test_soft_deleted_payment_is_excluded_from_view_total_paid(uow):
    s = uow.session
    student, enr, _ = _student_with_enrollment(s, 500)
    r = _receipt(s)
    _line(s, r, student.id, enr.id, 200)
    _line(s, r, student.id, enr.id, 100, deleted_at=datetime.now(timezone.utc))

    paid, remaining = _view(s, enr.id)
    assert paid == 200 and remaining == 300


def test_soft_deleted_refund_is_excluded_from_get_total_refunded(uow):
    s = uow.session
    student, enr, _ = _student_with_enrollment(s, 500)
    r = _receipt(s)
    pay = _line(s, r, student.id, enr.id, 300)
    _line(s, r, student.id, enr.id, 50, "refund", original_payment_id=pay.id)
    _line(s, r, student.id, enr.id, 70, "refund", original_payment_id=pay.id,
          deleted_at=datetime.now(timezone.utc))

    assert PaymentRepository(s).get_total_refunded(pay.id) == Decimal("50")


# ── #254 ──────────────────────────────────────────────────────────────────────

def test_receipt_debt_ignores_dropped_enrollment(uow):
    s = uow.session
    student, active, group_id = _student_with_enrollment(s, 500)
    create_test_enrollment(s, student.id, group_id, level_number=2,
                           status="dropped", amount_due=500)
    r = _receipt(s)
    _line(s, r, student.id, active.id, 500)

    assert ReceiptGenerationService(uow)._receipts.get_student_remaining_debt(student.id) == 0
    assert ReportsRepository(s).get_student_remaining_debt(student.id) == 0
    assert "Remaining Balance" not in ReceiptGenerationService(uow).generate_receipt_text(r.id)


def test_credit_on_one_enrollment_does_not_hide_debt_on_another(uow):
    s = uow.session
    student, owing, _ = _student_with_enrollment(s, 500)
    _, other_group, _, _ = create_minimal_group_bundle(s)
    credit = create_test_enrollment(s, student.id, other_group.id, amount_due=100)
    r = _receipt(s)
    _line(s, r, student.id, owing.id, 100)
    _line(s, r, student.id, credit.id, 300)  # 200 over-paid

    assert ReceiptGenerationService(uow)._receipts.get_student_remaining_debt(student.id) == 400
    assert ReportsRepository(s).get_student_remaining_debt(student.id) == 400
    assert "Remaining Balance: $400.00" in ReceiptGenerationService(uow).generate_receipt_text(r.id)


def test_refund_receipt_total_is_negative_in_text_detail_and_pdf(uow, monkeypatch):
    s = uow.session
    student, enr, _ = _student_with_enrollment(s, 500)
    pay = _line(s, _receipt(s), student.id, enr.id, 300)
    refund_receipt = _receipt(s)
    _line(s, refund_receipt, student.id, enr.id, 100, "refund", original_payment_id=pay.id)

    text_out = ReceiptGenerationService(uow).generate_receipt_text(refund_receipt.id)
    assert "TOTAL PAID:" in text_out and "$-100.00" in text_out

    svc = ReceiptService(uow)
    assert svc.get_detail(refund_receipt.id).total == Decimal("-100")

    captured = {}
    monkeypatch.setattr(
        "app.modules.finance.services.receipt_service.build_receipt_pdf",
        lambda **kw: captured.update(kw) or b"pdf",
    )
    svc.generate_pdf(refund_receipt.id)
    assert captured["total"] == -100.0


# ── #267 ──────────────────────────────────────────────────────────────────────

def test_group_enrollment_history_remaining_counts_refunds(uow):
    s = uow.session
    student, enr, group_id = _student_with_enrollment(s, 500)
    r = _receipt(s)
    pay = _line(s, r, student.id, enr.id, 300)
    _line(s, r, student.id, enr.id, 100, "refund", original_payment_id=pay.id)

    item = GroupAnalyticsService(uow).get_enrollment_history(group_id).enrollments[0]
    assert item.balance_remaining == 300
    assert item.payments_made == 200
