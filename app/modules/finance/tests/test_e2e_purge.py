"""Staging-only E2E purge (#218): guards, route registration, and the FK-safe delete.

The delete tests run the use case over the rollback-only ``uow`` fixture; the guard tests
drive the real route through a fresh app built with ``APP_ENVIRONMENT=staging``.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.main import create_app
from app.core.config import settings
from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupCourseHistory, GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.session_models import CourseSession
from app.modules.attendance.models.attendance_models import Attendance
from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models import Parent, Student, StudentParent
from app.modules.crm.models.activity_models import StudentActivityLog
from app.modules.enrollments.models import Enrollment, EnrollmentLevelHistory
from app.modules.finance.models import Payment, Receipt
from app.modules.finance.services.e2e_purge_service import E2EPurgeService
from app.testing import db_helpers as h

SECRET = "purge-secret"
STAGING_REF = "stagingref0123456789"
STAGING_URL = f"postgresql://postgres.{STAGING_REF}:pw@aws-0-eu.pooler.supabase.com:5432/postgres"

TABLES = {
    "students": Student, "parents": Parent, "student_parents": StudentParent,
    "student_activity_log": StudentActivityLog, "courses": Course, "groups": Group,
    "group_levels": GroupLevel, "group_course_history": GroupCourseHistory,
    "sessions": CourseSession, "enrollments": Enrollment,
    "enrollment_level_history": EnrollmentLevelHistory, "attendance": Attendance,
    "payments": Payment, "receipts": Receipt, "competitions": Competition,
    "teams": Team, "team_members": TeamMember,
}


def _seed(session, tag: str, run: str) -> dict[str, list[int]]:
    """A full set named ``<tag>-<run>-...``; returns ids per table."""
    n = f"{tag}-{run}"
    ph = lambda: f"+2010{uuid.uuid4().int % 10**8:08d}"  # noqa: E731
    course, group, level, sessions = h.create_minimal_group_bundle(
        session, course_name=f"{n}-course", group_name=f"{n}-group", session_count=2
    )
    session.add(GroupCourseHistory(group_id=group.id, course_id=course.id))
    parent = h.create_test_parent(session, full_name=f"{n}-parent", phone_primary=ph())
    student = h.create_test_student(session, full_name=f"{n}-student", parent_id=parent.id, phone=ph())
    session.add(StudentActivityLog(student_id=student.id, activity_type="note", description="x"))
    enr = h.create_test_enrollment(session, student_id=student.id, group_id=group.id, amount_due=500)
    session.add(EnrollmentLevelHistory(enrollment_id=enr.id, group_level_id=level.id, student_id=student.id))
    att = h.create_test_attendance(session, student.id, sessions[0].id, enr.id)
    receipt = h.create_test_receipt(session, payer_name=f"{n}-payer")
    pay = h.create_test_payment(session, receipt.id, student.id, 300, enrollment_id=enr.id)
    refund = h.create_test_payment(
        session, receipt.id, student.id, -100, enrollment_id=enr.id, transaction_type="refund"
    )
    refund.original_payment_id = pay.id
    orphan = h.create_test_receipt(session, payer_name=f"{n}-orphan")
    comp = h.create_test_competition(session, name=f"{n}-comp")
    team = h.create_test_team(session, comp.id, team_name=f"{n}-team")
    member = h.create_test_team_member(session, team.id, student.id, amount_due=50)
    fee_receipt = h.create_test_receipt(session, payer_name="someone")
    fee = h.create_test_payment(
        session, fee_receipt.id, student.id, 50, team_member_id=member.id, payment_type="competition"
    )
    session.commit()
    return {
        "students": [student.id], "parents": [parent.id], "student_parents": [student.id],
        "student_activity_log": [student.id], "courses": [course.id], "groups": [group.id],
        "group_levels": [level.id], "group_course_history": [group.id],
        "sessions": [s.id for s in sessions], "enrollments": [enr.id],
        "enrollment_level_history": [enr.id], "attendance": [att.id],
        "payments": [pay.id, refund.id, fee.id],
        "receipts": [receipt.id, orphan.id, fee_receipt.id],
        "competitions": [comp.id], "teams": [team.id], "team_members": [member.id],
    }


def _count(session, name: str, ids: list[int]) -> int:
    model = TABLES[name]
    by_fk = {
        "student_parents": "student_id", "student_activity_log": "student_id",
        "group_course_history": "group_id", "enrollment_level_history": "enrollment_id",
    }
    col = getattr(model, by_fk.get(name, "id"))
    return session.execute(select(func.count()).select_from(model).where(col.in_(ids))).scalar_one()


def _present(session, seed: dict[str, list[int]]) -> int:
    return sum(_count(session, name, ids) for name, ids in seed.items())


def test_purge_deletes_the_run_and_nothing_else(uow):
    run = uuid.uuid4().hex[:8]
    mine = _seed(uow.session, "e2e", run)
    other_run = _seed(uow.session, "e2e", uuid.uuid4().hex[:8])
    control = _seed(uow.session, "real", run)  # same run id, no e2e- prefix

    result = E2EPurgeService(uow).purge(run)

    assert result.prefix == f"e2e-{run}-"
    assert _present(uow.session, mine) == 0
    assert _present(uow.session, other_run) == sum(len(v) for v in other_run.values())
    assert _present(uow.session, control) == sum(len(v) for v in control.values())
    assert result.counts["students"] == 1 and result.counts["groups"] == 1
    assert result.counts["payments"] == 3 and result.counts["receipts"] == 3
    assert result.counts["sessions"] == 2 and result.counts["attendance"] == 1
    assert result.counts["team_members"] == 1 and result.counts["courses"] == 1
    assert E2EPurgeService(uow).purge(run).counts["students"] == 0  # idempotent


def test_run_id_that_prefixes_another_run_leaves_that_run(uow):
    run = uuid.uuid4().hex[:8]
    longer = _seed(uow.session, "e2e", run + "x")  # e2e-<run>x-... must not match run <run>
    _seed(uow.session, "e2e", run)
    E2EPurgeService(uow).purge(run)
    assert _present(uow.session, longer) == sum(len(v) for v in longer.values())


def test_purge_without_run_id_takes_every_e2e_run(uow):
    a = _seed(uow.session, "e2e", uuid.uuid4().hex[:8])
    b = _seed(uow.session, "e2e", uuid.uuid4().hex[:8])
    control = _seed(uow.session, "real", uuid.uuid4().hex[:8])
    E2EPurgeService(uow).purge(None)
    assert _present(uow.session, a) == _present(uow.session, b) == 0
    assert _present(uow.session, control) == sum(len(v) for v in control.values())


def test_receipt_shared_with_a_non_e2e_payment_is_kept(uow):
    run = uuid.uuid4().hex[:8]
    s = uow.session
    course, group, _level, _sessions = h.create_minimal_group_bundle(s, course_name=f"e2e-{run}-c", group_name=f"e2e-{run}-g")
    e2e_student = h.create_test_student(s, full_name=f"e2e-{run}-s", phone=f"+2011{uuid.uuid4().int % 10**8:08d}")
    real_student = h.create_test_student(s, full_name=f"real-{run}-s", phone=f"+2012{uuid.uuid4().int % 10**8:08d}")
    receipt = h.create_test_receipt(s, payer_name="shared")
    h.create_test_payment(s, receipt.id, e2e_student.id, 10)
    keep = h.create_test_payment(s, receipt.id, real_student.id, 20)

    E2EPurgeService(uow).purge(run)

    assert s.get(Payment, keep.id) is not None and s.get(Receipt, receipt.id) is not None
    assert s.get(Student, real_student.id) is not None


# ── guards ────────────────────────────────────────────────────────────────────

@pytest.fixture
def staging_client(monkeypatch, uow):
    """A fresh app built as staging (route registered), pointed at the staging ref."""
    from app.api.deps import get_uow

    monkeypatch.setattr(settings, "app_environment", "staging")
    monkeypatch.setattr(settings, "staging_project_ref", STAGING_REF)
    monkeypatch.setattr(settings, "database_url", STAGING_URL)
    monkeypatch.setattr(settings, "e2e_purge_secret", SECRET)
    app = create_app()
    app.dependency_overrides[get_uow] = lambda: uow
    return TestClient(app), uow


def _post(client, secret=SECRET, run_id=None):
    headers = {"X-E2E-Purge-Secret": secret} if secret is not None else {}
    return client.post("/api/v1/internal/e2e/purge", params={"run_id": run_id} if run_id else None, headers=headers)


def test_route_absent_unless_staging(monkeypatch):
    monkeypatch.setattr(settings, "app_environment", "production")
    assert _post(TestClient(create_app())).status_code == 404
    monkeypatch.setattr(settings, "app_environment", "")
    assert _post(TestClient(create_app())).status_code == 404


def test_happy_path_over_http(staging_client):
    client, uow = staging_client
    run = uuid.uuid4().hex[:8]
    seed = _seed(uow.session, "e2e", run)
    res = _post(client, run_id=run)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True and body["data"]["counts"]["students"] == 1
    assert _present(uow.session, seed) == 0


@pytest.mark.parametrize("field,value", [
    ("app_environment", "production"),
    ("app_environment", ""),
    ("staging_project_ref", ""),
    ("staging_project_ref", "otherref0123456789ab"),
])
def test_wrong_target_is_403_and_deletes_nothing(staging_client, monkeypatch, field, value):
    client, uow = staging_client
    run = uuid.uuid4().hex[:8]
    seed = _seed(uow.session, "e2e", run)
    monkeypatch.setattr(settings, field, value)  # route is registered; the handler guard still refuses
    res = _post(client, run_id=run)
    assert res.status_code == 403
    assert res.json()["error"] == "ForbiddenError"
    assert _present(uow.session, seed) == sum(len(v) for v in seed.values())


@pytest.mark.parametrize("secret", [None, "wrong"])
def test_bad_secret_is_401(staging_client, secret):
    client, uow = staging_client
    seed = _seed(uow.session, "e2e", (run := uuid.uuid4().hex[:8]))
    assert _post(client, secret=secret, run_id=run).status_code == 401
    assert _present(uow.session, seed) == sum(len(v) for v in seed.values())


def test_unconfigured_secret_is_401_even_for_an_empty_header(staging_client, monkeypatch):
    client, _uow = staging_client
    monkeypatch.setattr(settings, "e2e_purge_secret", "")
    assert _post(client, secret="").status_code == 401
