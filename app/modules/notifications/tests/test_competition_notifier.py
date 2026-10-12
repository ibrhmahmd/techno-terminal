"""CompetitionNotifier port wiring and behaviour (ADR-0007, ticket #34)."""

import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.db.connection import get_session
from app.db.uow import unit_of_work
from app.modules.competitions import CompetitionNotifier, TeamRegistrationService
from app.modules.competitions.api.deps import get_competition_notifier as competitions_deps_get_notifier
from app.modules.competitions.models import Competition
from app.modules.competitions.schemas import RegisterTeamInput
from app.modules.crm.models.student_models import Student
from app.modules.notifications.adapters import get_competition_notifier as adapters_get_notifier
from app.modules.competitions.tests.fakes import FakeCompetitionNotifier


def _short() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture
def seeded():
    with get_session() as s:
        comp = Competition(name=f"Notif {_short()}", edition_year=2026, competition_date=date(2026, 5, 1))
        student = Student(full_name=f"Notif {_short()}", phone=f"555{_short()[:7]}", status="active")
        s.add(comp)
        s.add(student)
        s.commit()
        s.refresh(comp)
        s.refresh(student)
        ids = {"comp": comp.id, "student": student.id}
    yield ids
    with get_session() as s:
        s.execute(text("delete from student_activity_log where student_id = :s"), {"s": ids["student"]})
        s.execute(text("delete from team_members where student_id = :s"), {"s": ids["student"]})
        s.execute(text("delete from teams where competition_id = :c"), {"c": ids["comp"]})
        s.execute(text("delete from competitions where id = :c"), {"c": ids["comp"]})
        s.execute(text("delete from students where id = :s"), {"s": ids["student"]})
        s.commit()


def test_fake_satisfies_the_port():
    notifier: CompetitionNotifier = FakeCompetitionNotifier()
    notifier.team_registration(
        student_id=1, team_id=2, team_name="t", competition_name="c", category="x", subcategory=None
    )
    assert notifier.calls[0][0] == "team_registration"


def test_create_app_overrides_the_notifier_with_the_adapter():
    from app.api.main import create_app

    app = create_app()
    assert app.dependency_overrides[competitions_deps_get_notifier] is adapters_get_notifier


def test_register_team_notifies_each_student_after_commit(seeded):
    fake = FakeCompetitionNotifier()
    with unit_of_work() as uow:
        result = TeamRegistrationService(uow, notifier=fake).register_team(
            RegisterTeamInput(
                competition_id=seeded["comp"], team_name=f"T {_short()}", category="Robotics",
                student_ids=[seeded["student"]],
            )
        )
    assert [c[0] for c in fake.calls] == ["team_registration"]
    assert fake.calls[0][1]["student_id"] == seeded["student"]
    assert fake.calls[0][1]["team_id"] == result.result.team.id


def test_notifier_failure_never_fails_registration(seeded):
    fake = FakeCompetitionNotifier(should_raise=True)
    with unit_of_work() as uow:
        result = TeamRegistrationService(uow, notifier=fake).register_team(
            RegisterTeamInput(
                competition_id=seeded["comp"], team_name=f"T {_short()}", category="Robotics",
                student_ids=[seeded["student"]],
            )
        )
    assert result.result.members_added == 1
