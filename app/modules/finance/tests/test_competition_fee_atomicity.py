"""Atomicity of competition fee payment (ADR-0001/0006, ticket #34).

``CompetitionFeeService.pay_competition_fee`` creates the receipt and payment
(finance), records the fee on the team member (competitions, via the facade) and
logs the activity (crm) in ONE transaction over a single ``UnitOfWork``. A forced
failure after the receipt exists must leave no receipt line, no payment and no fee
update. Seeding is committed and uuid-tagged; a real ``unit_of_work()`` is used so
a real commit/rollback is exercised. Teardown deletes what the test created.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlmodel import select

from app.db.connection import get_session
from app.db.uow import unit_of_work
from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models.student_models import Student
from app.modules.finance.models.payment import Payment
from app.modules.finance.schemas.competition_fee import PayCompetitionFeeInput
from app.modules.finance.services.competition_fee_service import CompetitionFeeService


def _short() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture
def seeded():
    with get_session() as s:
        comp = Competition(name=f"Atomic {_short()}", edition_year=2026, competition_date=date(2026, 5, 1))
        s.add(comp)
        s.commit()
        s.refresh(comp)
        team = Team(competition_id=comp.id, team_name=f"T {_short()}", category="Robotics")
        s.add(team)
        student = Student(full_name=f"Atomic {_short()}", phone=f"555{_short()[:7]}", status="active")
        s.add(student)
        s.commit()
        s.refresh(team)
        s.refresh(student)
        member = TeamMember(team_id=team.id, student_id=student.id, amount_due=100.0, amount_paid=0.0)
        s.add(member)
        s.commit()
        s.refresh(member)
        ids = {"comp": comp.id, "team": team.id, "student": student.id, "member": member.id}
    yield ids
    with get_session() as s:
        pay_ids = [p.id for p in s.exec(select(Payment).where(Payment.team_member_id == ids["member"])).all()]
        receipt_ids = [
            r[0] for r in s.execute(
                text("select distinct receipt_id from payments where team_member_id = :m"), {"m": ids["member"]}
            ).all()
        ]
        s.execute(text("delete from student_activity_log where student_id = :s"), {"s": ids["student"]})
        if pay_ids:
            s.execute(text("delete from payments where team_member_id = :m"), {"m": ids["member"]})
        if receipt_ids:
            s.execute(text("delete from receipts where id = any(:r)"), {"r": receipt_ids})
        s.execute(text("delete from team_members where id = :m"), {"m": ids["member"]})
        s.execute(text("delete from teams where id = :t"), {"t": ids["team"]})
        s.execute(text("delete from competitions where id = :c"), {"c": ids["comp"]})
        s.execute(text("delete from students where id = :s"), {"s": ids["student"]})
        s.commit()


def _state(ids):
    with get_session() as s:
        payments = s.exec(select(Payment).where(Payment.team_member_id == ids["member"])).all()
        member = s.get(TeamMember, ids["member"])
        return len(payments), float(member.amount_paid)


def test_failure_after_receipt_rolls_everything_back(seeded):
    cmd = PayCompetitionFeeInput(team_id=seeded["team"], student_id=seeded["student"], amount=40.0)

    with pytest.raises(RuntimeError, match="boom after receipt"):
        with unit_of_work() as uow:
            svc = CompetitionFeeService(uow)
            original = svc._team_fees.record_payment

            def record_then_fail(member_id, amount):
                original(member_id, amount)
                raise RuntimeError("boom after receipt")

            svc._team_fees.record_payment = record_then_fail
            svc.pay_competition_fee(cmd)

    assert _state(seeded) == (0, 0.0)


def test_success_persists_receipt_payment_and_fee(seeded):
    cmd = PayCompetitionFeeInput(team_id=seeded["team"], student_id=seeded["student"], amount=40.0)

    with unit_of_work() as uow:
        result = CompetitionFeeService(uow).pay_competition_fee(cmd)

    assert result.amount_paid == 40.0
    assert _state(seeded) == (1, 40.0)
