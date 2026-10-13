"""TaskNotificationService processors reach the dispatcher (#153).

They read the acting user's name; ``User`` has no ``email`` field, so they used
to raise ``AttributeError`` in the background and never send. The processors
open their own session, so the rows are committed through ``db_session``.
"""
import asyncio
import uuid
from types import SimpleNamespace

import pytest

from app.modules.auth.models.auth_models import User
from app.modules.notifications.services.task_notifications import TaskNotificationService
from app.modules.tasks.models.task import Task, TaskComment
from app.modules.tasks.tests.characterization.test_tasks_api import _make_employee


@pytest.fixture
def rows(db_session):
    emp = _make_employee(db_session)
    user = User(username=f"actor_{uuid.uuid4().hex[:8]}@test.com", role="admin", is_active=True)
    db_session.add(user)
    db_session.commit()
    task = Task(title=f"T {uuid.uuid4().hex[:8]}", assigned_to=emp.id, assigned_by=user.id)
    db_session.add(task)
    db_session.commit()
    comment = TaskComment(task_id=task.id, author_id=user.id, content="hello")
    db_session.add(comment)
    db_session.commit()
    return emp, user, task, comment


@pytest.fixture
def svc(monkeypatch):
    service = TaskNotificationService(repo=None)
    sent = []

    async def fake_dispatch(**kwargs):
        sent.append(kwargs)
        return True

    monkeypatch.setattr(service, "_get_template_by_name", lambda name: SimpleNamespace(name=name, is_active=True))
    monkeypatch.setattr(service, "_resolve_notification_recipients", lambda **kw: [])
    monkeypatch.setattr(service, "_dispatch", fake_dispatch)
    service.sent = sent
    return service


def test_task_assigned_email_is_dispatched(svc, rows):
    emp, user, task, _ = rows

    asyncio.run(svc._process_task_assigned(str(task.id), emp.id, user.id))

    assert len(svc.sent) == 1
    assert svc.sent[0]["contact"] == emp.email
    assert svc.sent[0]["variables"]["assigned_by_name"] == user.username


def test_status_changed_email_is_dispatched(svc, rows):
    emp, user, task, _ = rows

    asyncio.run(svc._process_status_changed(str(task.id), emp.id, "todo", "done", user.id))

    assert len(svc.sent) == 1
    assert svc.sent[0]["variables"]["changed_by_name"] == user.username


def test_comment_added_email_is_dispatched(svc, rows):
    emp, user, task, comment = rows

    asyncio.run(svc._process_comment_added(str(task.id), str(comment.id), user.id))

    assert len(svc.sent) == 1
    assert svc.sent[0]["variables"]["author_name"] == user.username
