"""Refund and payment guards: #260 (remove refunded member), #241 (refund-of-refund,
refund race), #245 (overpayment guard). Most tests use the rollback-only ``uow``;
the race tests commit real rows through ``unit_of_work`` and clean them up."""

import threading
import time
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.db.connection import get_session
from app.db.uow import unit_of_work
from app.modules.competitions import TeamRosterService
from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models.student_models import Student
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.modules.finance.schemas import IssueRefundDTO
from app.modules.finance.schemas.competition_fee import PayCompetitionFeeInput
from app.modules.finance.schemas.receipt_line_input import ReceiptLineInput
from app.modules.finance.services.balance_service import BalanceService
from app.modules.finance.services.competition_fee_service import CompetitionFeeService
from app.modules.finance.services.refund_service import RefundService
from app.shared.exceptions import BusinessRuleError
from app.testing.db_helpers import create_minimal_group_bundle, create_student_with_enrollment


def _tag() -> str:
    return uuid.uuid4().hex[:10]


def _seed(session, due=100.0) -> dict:
    comp = Competition(name=f"RG {_tag()}", edition_year=2026, competition_date=date(2026, 5, 1))
    session.add(comp)
    session.flush()
    team = Team(competition_id=comp.id, team_name=f"T {_tag()}", category="Robotics")
    student = Student(full_name=f"RG {_tag()}", phone=f"555{_tag()[:7]}", status="active")
    session.add_all([team, student])
    session.flush()
    member = TeamMember(team_id=team.id, student_id=student.id, amount_due=due, amount_paid=0.0)
    session.add(member)
    session.flush()
    return {"comp": comp.id, "team": team.id, "student": student.id, "member": member.id}


def _pay(uow, ids, amount=100.0):
    return CompetitionFeeService(uow).pay_competition_fee(
        PayCompetitionFeeInput(team_id=ids["team"], student_id=ids["student"], amount=amount)
    )


def _refund_dto(payment_id, amount=100):
    return IssueRefundDTO(payment_id=payment_id, amount=Decimal(amount), reason="t", received_by_user_id=None)


# ── #260 ──────────────────────────────────────────────────────────────────────

def test_remove_fully_refunded_member_is_409(uow):
    ids = _seed(uow.session)
    _pay(uow, ids)
    CompetitionFeeService(uow).refund_competition_fee(ids["team"], ids["student"], 100.0)

    with pytest.raises(BusinessRuleError, match="payment history"):
        TeamRosterService(uow).remove_team_member(ids["team"], ids["student"])


def test_remove_member_without_payments_works(uow):
    ids = _seed(uow.session)
    assert TeamRosterService(uow).remove_team_member(ids["team"], ids["student"]) is True


# ── #241 ──────────────────────────────────────────────────────────────────────

def test_refund_of_a_refund_is_409(uow):
    ids = _seed(uow.session)
    pid = _pay(uow, ids).payment_id
    RefundService(uow).issue(_refund_dto(pid, 40))
    refund_id = uow.session.execute(
        text("select id from payments where original_payment_id = :p"), {"p": pid}
    ).scalar()

    with pytest.raises(BusinessRuleError, match="not a refund"):
        RefundService(uow).issue(_refund_dto(refund_id, 10))


@pytest.fixture
def committed_payment():
    with unit_of_work() as uow:
        ids = _seed(uow.session)
        uow.commit()
    with unit_of_work() as uow:
        ids["payment"] = _pay(uow, ids).payment_id
    yield ids
    with get_session() as s:
        s.execute(text("delete from student_activity_log where student_id = :s"), {"s": ids["student"]})
        rids = [r[0] for r in s.execute(
            text("select distinct receipt_id from payments where team_member_id = :m"), {"m": ids["member"]}
        ).all()]
        s.execute(text("delete from payments where team_member_id = :m"), {"m": ids["member"]})
        s.execute(text("delete from receipts where id = any(:r)"), {"r": rids})
        s.execute(text("delete from team_members where id = :m"), {"m": ids["member"]})
        s.execute(text("delete from teams where id = :t"), {"t": ids["team"]})
        s.execute(text("delete from competitions where id = :c"), {"c": ids["comp"]})
        s.execute(text("delete from students where id = :s"), {"s": ids["student"]})
        s.commit()


def _total_refunded(ids) -> Decimal:
    with unit_of_work() as uow:
        return PaymentRepository(uow.session).get_total_refunded(ids["payment"])


def test_refund_waits_for_the_row_lock(committed_payment):
    """A holds the payment's row lock; B's refund must block until A lets go (proves FOR UPDATE)."""
    ids = committed_payment
    outcome = {}

    def refund_b():
        try:
            with unit_of_work() as uow:
                RefundService(uow).issue(_refund_dto(ids["payment"]))
            outcome["b"] = "ok"
        except Exception as e:  # noqa: BLE001
            outcome["b"] = e

    with unit_of_work() as a:
        PaymentRepository(a.session).get_for_update(ids["payment"])
        t = threading.Thread(target=refund_b)
        t.start()
        time.sleep(1.0)
        assert t.is_alive(), "refund did not wait for the row lock"
    t.join(timeout=10)
    assert outcome["b"] == "ok"
    assert _total_refunded(ids) == Decimal(100)


def test_concurrent_full_refunds_only_one_succeeds(committed_payment):
    ids = committed_payment
    barrier = threading.Barrier(2)
    results = []

    def worker():
        try:
            with unit_of_work() as uow:
                barrier.wait(timeout=10)
                RefundService(uow).issue(_refund_dto(ids["payment"]))
            results.append("ok")
        except BusinessRuleError:
            results.append("rejected")

    threads = [threading.Thread(target=worker) for _ in range(2)]
    [t.start() for t in threads]
    [t.join(timeout=20) for t in threads]

    assert sorted(results) == ["ok", "rejected"]
    assert _total_refunded(ids) == Decimal(100)


# ── #245 ──────────────────────────────────────────────────────────────────────

def _enrollment(uow, due=1000.0):
    _, group, level, _ = create_minimal_group_bundle(uow.session)
    _, student, enrollment = create_student_with_enrollment(
        uow.session, group_id=group.id, level_number=level.level_number, amount_due=due
    )
    uow.session.flush()
    return student.id, enrollment.id


def test_split_lines_over_the_debt_are_flagged(uow):
    sid, eid = _enrollment(uow)
    lines = [ReceiptLineInput(student_id=sid, enrollment_id=eid, amount=600.0) for _ in range(2)]

    risks = BalanceService(uow).assess_overpayment_risk(lines)

    assert len(risks) == 1
    assert risks[0].amount == Decimal(1200)
    assert risks[0].excess_credit == Decimal(200)


def test_exact_payment_is_not_flagged(uow):
    sid, eid = _enrollment(uow)
    lines = [ReceiptLineInput(student_id=sid, enrollment_id=eid, amount=a) for a in (400.0, 600.0)]

    assert BalanceService(uow).assess_overpayment_risk(lines) == []


def test_competition_overpay_is_409_and_exact_is_ok(uow):
    ids = _seed(uow.session, due=500.0)

    with pytest.raises(BusinessRuleError, match="outstanding"):
        _pay(uow, ids, amount=5000.0)

    assert _pay(uow, ids, amount=500.0).amount_paid == 500.0
