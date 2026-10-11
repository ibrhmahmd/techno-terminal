"""TaskNotifier port wiring and behaviour (ADR-0007, ticket #23)."""

import uuid

from app.modules.tasks import CreateTaskInput, TaskNotifier, TaskService, UpdateTaskInput
from app.modules.tasks.api.deps import get_task_notifier as tasks_deps_get_notifier
from app.modules.notifications.adapters import get_task_notifier as adapters_get_notifier
from tests.characterization.test_tasks_api import _make_employee
from tests.utils.task_notifier_fake import FakeTaskNotifier


def test_fake_satisfies_the_port():
    notifier: TaskNotifier = FakeTaskNotifier()
    notifier.task_assigned(task_id=uuid.uuid4(), employee_id=1, assigned_by_user_id=2)
    assert notifier.calls[0][0] == "task_assigned"


def test_create_app_overrides_the_notifier_with_the_adapter():
    from app.api.main import create_app

    app = create_app()
    assert app.dependency_overrides[tasks_deps_get_notifier] is adapters_get_notifier


def _admin(db_session):
    from app.modules.auth.models.auth_models import User

    return db_session.query(User).filter(User.role == "admin").first()


def test_create_assigned_task_notifies_after_commit(uow, db_session):
    emp = _make_employee(db_session)
    fake = FakeTaskNotifier()

    detail = TaskService(uow, notifier=fake).create_task(
        CreateTaskInput(title=f"T {uuid.uuid4().hex[:8]}", assigned_to=emp.id), _admin(db_session)
    )

    assert [c[0] for c in fake.calls] == ["task_assigned"]
    assert fake.calls[0][1]["task_id"] == detail.id
    assert fake.calls[0][1]["employee_id"] == emp.id


def test_status_change_notifies_and_failure_is_swallowed(uow, db_session):
    emp = _make_employee(db_session)
    admin = _admin(db_session)
    svc = TaskService(uow, notifier=FakeTaskNotifier(should_raise=True))
    detail = svc.create_task(CreateTaskInput(title=f"T {uuid.uuid4().hex[:8]}", assigned_to=emp.id), admin)

    updated = svc.update_task(detail.id, UpdateTaskInput(status="done"), admin)

    assert updated.status == "done"
