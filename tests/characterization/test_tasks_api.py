"""Characterization tests for the Tasks HTTP API (ticket #23).

Pins status codes, envelopes and field shapes of the eleven endpoints served by
``app/api/routers/tasks.py`` BEFORE the HTTP layer moves into ``app/modules/tasks/``:

    POST/GET /tasks, GET/PATCH/DELETE /tasks/{id}, POST /tasks/{id}/subtasks,
    PATCH/DELETE /tasks/subtasks/{id}, POST /tasks/{id}/comments,
    DELETE /tasks/comments/{id}, POST /tasks/{id}/time-logs

Buckets
-------
* The tasks service runs on the request ``get_db`` session and really commits, so
  tests create their tasks through the API and read them back through the API.
* Writes can send notifications: ``get_notification_service`` is replaced by a
  no-op so no real mail/SMS can go out.
* Employee (non-admin) behaviour is exercised by overriding ``get_current_user`` with
  a detached ``User`` whose role is ``employee`` and whose ``employee_id`` points at
  a committed employee (no such role exists in the auth enum, but the service only
  checks ``is_admin``).

Pinned quirks (pinned, not endorsed)
------------------------------------
See the tests marked "current behaviour".
"""

import uuid

import pytest

from app.modules.auth.models.auth_models import User
from app.modules.hr.models import Employee


class _Noop:
    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return None


@pytest.fixture
def noop_notifications(app):
    from app.api.dependencies import get_notification_service

    svc = _Noop()
    app.dependency_overrides[get_notification_service] = lambda: svc
    try:
        yield svc
    finally:
        app.dependency_overrides.pop(get_notification_service, None)


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_employee(db_session) -> Employee:
    emp = Employee(
        full_name=f"Task Emp {_short()}", phone=f"+201{_short()}", email=f"{_short()}@test.com",
        national_id=f"NID{_short()}", university="Test University", major="CS", is_graduate=False,
        job_title="Instructor", employment_type="full_time", monthly_salary=5000.0, is_active=True,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return emp


@pytest.fixture
def employee_auth(app, db_session):
    """Authenticate as a non-admin user bound to a fresh employee. Yields (employee, user)."""
    from app.api.dependencies import get_current_user

    emp = _make_employee(db_session)
    admin = db_session.query(User).filter(User.supabase_uid == "test-admin-001").first()
    user = User.model_construct(
        id=admin.id if admin else 1, username=f"emp_{_short()}", role="employee",
        is_active=True, employee_id=emp.id,
    )

    async def _who():
        return user

    app.dependency_overrides[get_current_user] = _who
    yield emp, user
    app.dependency_overrides.pop(get_current_user, None)


_TASK_FIELDS = {
    "id", "title", "description", "due_date", "priority", "status", "assigned_to",
    "assigned_to_name", "assigned_by", "assigned_by_name", "estimated_hours", "tags",
    "is_recurring", "recurrence_pattern", "parent_task_id", "created_at", "updated_at",
}
_DETAIL_FIELDS = _TASK_FIELDS | {"subtasks", "comments", "time_logs"}


def _create(client, headers, **body):
    payload = {"title": f"Task {_short()}"}
    payload.update(body)
    return client.post("/api/v1/tasks", headers=headers, json=payload)


# ── POST /tasks ───────────────────────────────────────────────────────────────


def test_create_task(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    r = _create(client_with_uow, mock_admin_headers, description="d", priority="high", tags=["a", "b"])

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["message"] == "Task created successfully"
    data = body["data"]
    assert set(data) == _DETAIL_FIELDS
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["tags"] == ["a", "b"]
    assert data["subtasks"] == [] and data["comments"] == [] and data["time_logs"] == []
    assert data["assigned_to"] is None


def test_create_task_assigned_to_employee(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    emp = _make_employee(db_session)

    r = _create(client_with_uow, mock_admin_headers, assigned_to=emp.id)

    assert r.status_code == 200
    assert r.json()["data"]["assigned_to"] == emp.id
    assert r.json()["data"]["assigned_to_name"] == emp.full_name


def test_create_task_unknown_assignee_is_404(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    r = _create(client_with_uow, mock_admin_headers, assigned_to=999999999)

    assert r.status_code == 404
    assert r.json()["error"] == "NotFoundError"
    assert r.json()["message"] == "Employee 999999999 not found."


def test_create_task_validation(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    assert client_with_uow.post("/api/v1/tasks", headers=h, json={}).status_code == 422
    assert client_with_uow.post("/api/v1/tasks", headers=h, json={"title": ""}).status_code == 422
    assert client_with_uow.post("/api/v1/tasks", headers=h, json={"title": "x", "priority": "nope"}).status_code == 422
    assert client_with_uow.post("/api/v1/tasks", headers=h, json={"title": "x", "status": "weird"}).status_code == 422


# ── GET /tasks ────────────────────────────────────────────────────────────────


def test_list_tasks_and_filters(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    emp = _make_employee(db_session)
    t = _create(client_with_uow, mock_admin_headers, assigned_to=emp.id, priority="low").json()["data"]
    _create(client_with_uow, mock_admin_headers)

    r = client_with_uow.get(f"/api/v1/tasks?assigned_to={emp.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Fetched 1 tasks"
    assert [x["id"] for x in body["data"]] == [t["id"]]
    assert set(body["data"][0]) == _TASK_FIELDS


def test_list_tasks_filter_validation(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.get("/api/v1/tasks?status=weird", headers=mock_admin_headers).status_code == 422
    assert client_with_uow.get("/api/v1/tasks?priority=nope", headers=mock_admin_headers).status_code == 422


# ── GET /tasks/{id} ───────────────────────────────────────────────────────────


def test_get_task(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    t = _create(client_with_uow, mock_admin_headers).json()["data"]

    r = client_with_uow.get(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert set(r.json()["data"]) == _DETAIL_FIELDS
    assert r.json()["data"]["id"] == t["id"]


def test_get_task_not_found(client_with_uow, override_auth, mock_admin_headers):
    missing = uuid.uuid4()
    r = client_with_uow.get(f"/api/v1/tasks/{missing}", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["message"] == f"Task {missing} not found."


def test_get_task_bad_id_is_422(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.get("/api/v1/tasks/not-a-uuid", headers=mock_admin_headers).status_code == 422


# ── PATCH /tasks/{id} ─────────────────────────────────────────────────────────


def test_update_task_as_admin(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    t = _create(client_with_uow, mock_admin_headers).json()["data"]

    r = client_with_uow.patch(
        f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers,
        json={"title": "Renamed", "status": "in_progress", "priority": "high"},
    )

    assert r.status_code == 200
    assert r.json()["message"] == "Task updated successfully"
    d = r.json()["data"]
    assert d["title"] == "Renamed" and d["status"] == "in_progress" and d["priority"] == "high"


def test_update_task_not_found(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    r = client_with_uow.patch(f"/api/v1/tasks/{uuid.uuid4()}", headers=mock_admin_headers, json={"title": "x"})
    assert r.status_code == 404


def test_update_task_employee_may_change_status_only(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    emp = _make_employee(db_session)
    t = _create(client_with_uow, mock_admin_headers, assigned_to=emp.id).json()["data"]
    from app.api.dependencies import get_current_user
    app = client_with_uow.app
    app.dependency_overrides[get_current_user] = _employee_override(db_session, emp)
    try:
        ok = client_with_uow.patch(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers, json={"status": "done"})
        bad = client_with_uow.patch(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers, json={"title": "hack"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert ok.status_code == 200 and ok.json()["data"]["status"] == "done"
    assert bad.status_code == 401
    assert bad.json()["message"] == "Employees can only update task status."


def _employee_override(db_session, emp):
    admin = db_session.query(User).filter(User.supabase_uid == "test-admin-001").first()
    user = User.model_construct(
        id=admin.id, username=f"emp_{_short()}", role="employee", is_active=True, employee_id=emp.id,
    )

    async def _who():
        return user

    return _who


def test_update_task_employee_not_assignee_is_401(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    emp = _make_employee(db_session)
    other = _make_employee(db_session)
    t = _create(client_with_uow, mock_admin_headers, assigned_to=other.id).json()["data"]
    from app.api.dependencies import get_current_user
    app = client_with_uow.app
    app.dependency_overrides[get_current_user] = _employee_override(db_session, emp)
    try:
        r = client_with_uow.patch(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers, json={"status": "done"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert r.status_code == 401
    assert r.json()["message"] == "You can only update tasks assigned to you."


# ── DELETE /tasks/{id} ────────────────────────────────────────────────────────


def test_delete_task_is_soft(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    t = _create(client_with_uow, mock_admin_headers).json()["data"]

    r = client_with_uow.delete(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] is True
    assert r.json()["message"] == "Task deleted successfully"
    assert client_with_uow.get(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers).status_code == 404


def test_delete_task_not_found(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.delete(f"/api/v1/tasks/{uuid.uuid4()}", headers=mock_admin_headers).status_code == 404


# ── Subtasks ──────────────────────────────────────────────────────────────────


def _seed_subtask(session, task_id: str):
    """Insert a subtask through the uow fixture's session (the tasks created through the API
    live in that transaction, so a separate committed session could not see them)."""
    from app.modules.tasks.models import TaskSubtask

    sub = TaskSubtask(task_id=uuid.UUID(task_id), title=f"sub {_short()}", is_done=False)
    session.add(sub)
    session.flush()
    session.refresh(sub)
    return sub


def test_add_subtask(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    t = _create(client_with_uow, mock_admin_headers).json()["data"]

    r = client_with_uow.post(f"/api/v1/tasks/{t['id']}/subtasks", headers=mock_admin_headers, json={"title": "step 1"})

    assert r.status_code == 200
    assert r.json()["message"] == "Subtask added successfully"
    sub = r.json()["data"]
    assert set(sub) == {"id", "task_id", "title", "is_done", "created_at", "updated_at"}
    assert sub["is_done"] is False and sub["task_id"] == t["id"] and sub["title"] == "step 1"


def test_update_subtask(client_with_uow, override_auth, mock_admin_headers, uow, noop_notifications):
    t = _create(client_with_uow, mock_admin_headers).json()["data"]
    sub = _seed_subtask(uow.session, t["id"])

    r = client_with_uow.patch(
        f"/api/v1/tasks/subtasks/{sub.id}", headers=mock_admin_headers, json={"is_done": True, "title": "renamed"}
    )

    assert r.status_code == 200
    assert r.json()["message"] == "Subtask updated successfully"
    assert r.json()["data"]["is_done"] is True and r.json()["data"]["title"] == "renamed"


def test_task_detail_with_subtasks_crashes_with_500(app, client_with_uow, override_auth, mock_admin_headers, uow, noop_notifications):
    """current behaviour (pinned, not endorsed): reading a task that has subtasks fails with 500,
    because the repository selects with ``sqlalchemy.select`` through a SQLModel session and the
    subtask rows come back as Row tuples that the detail DTO cannot validate."""
    from fastapi.testclient import TestClient

    t = _create(client_with_uow, mock_admin_headers).json()["data"]
    _seed_subtask(uow.session, t["id"])

    r = TestClient(app, raise_server_exceptions=False).get(f"/api/v1/tasks/{t['id']}", headers=mock_admin_headers)

    assert r.status_code == 500


def test_delete_subtask(app, client_with_uow, override_auth, mock_admin_headers, uow, noop_notifications):
    from fastapi.testclient import TestClient

    t = _create(client_with_uow, mock_admin_headers).json()["data"]
    sub = _seed_subtask(uow.session, t["id"])

    r = TestClient(app, raise_server_exceptions=False).delete(
        f"/api/v1/tasks/subtasks/{sub.id}", headers=mock_admin_headers
    )

    assert r.status_code == 200


def test_subtask_not_found_cases(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    assert client_with_uow.post(f"/api/v1/tasks/{uuid.uuid4()}/subtasks", headers=h, json={"title": "x"}).status_code == 404
    assert client_with_uow.patch(f"/api/v1/tasks/subtasks/{uuid.uuid4()}", headers=h, json={"is_done": True}).status_code == 404
    assert client_with_uow.delete(f"/api/v1/tasks/subtasks/{uuid.uuid4()}", headers=h).status_code == 404
    assert client_with_uow.post(f"/api/v1/tasks/{uuid.uuid4()}/subtasks", headers=h, json={"title": ""}).status_code == 422


# ── Comments ──────────────────────────────────────────────────────────────────


def test_comment_add_and_delete(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    t = _create(client_with_uow, mock_admin_headers).json()["data"]

    add = client_with_uow.post(f"/api/v1/tasks/{t['id']}/comments", headers=mock_admin_headers, json={"content": "hello"})
    assert add.status_code == 200
    c = add.json()["data"]
    assert set(c) == {"id", "task_id", "author_id", "author_name", "content", "created_at", "updated_at"}
    assert c["content"] == "hello" and c["task_id"] == t["id"]
    assert add.json()["message"] == "Comment added successfully"

    dele = client_with_uow.delete(f"/api/v1/tasks/comments/{c['id']}", headers=mock_admin_headers)
    assert dele.status_code == 200 and dele.json()["data"] is True
    assert dele.json()["message"] == "Comment deleted successfully"


def test_comment_not_found_and_validation(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    h = mock_admin_headers
    assert client_with_uow.post(f"/api/v1/tasks/{uuid.uuid4()}/comments", headers=h, json={"content": "x"}).status_code == 404
    assert client_with_uow.delete(f"/api/v1/tasks/comments/{uuid.uuid4()}", headers=h).status_code == 404
    t = _create(client_with_uow, h).json()["data"]
    assert client_with_uow.post(f"/api/v1/tasks/{t['id']}/comments", headers=h, json={"content": ""}).status_code == 422


# ── Time logs ─────────────────────────────────────────────────────────────────


def test_time_log_requires_assignee(client_with_uow, override_auth, mock_admin_headers, noop_notifications):
    """current behaviour (pinned, not endorsed): even an admin cannot log time on a task that is
    not assigned to them (the admin test user has no employee_id)."""
    t = _create(client_with_uow, mock_admin_headers).json()["data"]

    r = client_with_uow.post(f"/api/v1/tasks/{t['id']}/time-logs", headers=mock_admin_headers, json={"hours": 1.5})

    assert r.status_code == 401
    assert r.json()["message"] == "You can only log time on tasks assigned to you."


def test_time_log_by_assignee(client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications):
    emp = _make_employee(db_session)
    t = _create(client_with_uow, mock_admin_headers, assigned_to=emp.id).json()["data"]
    from app.api.dependencies import get_current_user
    app = client_with_uow.app
    app.dependency_overrides[get_current_user] = _employee_override(db_session, emp)
    try:
        r = client_with_uow.post(
            f"/api/v1/tasks/{t['id']}/time-logs", headers=mock_admin_headers, json={"hours": 2.5, "note": "worked"}
        )
        bad = client_with_uow.post(f"/api/v1/tasks/{t['id']}/time-logs", headers=mock_admin_headers, json={"hours": 0})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert r.status_code == 200
    log = r.json()["data"]
    assert set(log) == {"id", "task_id", "employee_id", "employee_name", "hours", "note", "logged_at", "created_at"}
    assert log["hours"] == 2.5 and log["note"] == "worked" and log["employee_id"] == emp.id
    assert r.json()["message"] == "Time logged successfully"
    assert bad.status_code == 422


def test_time_log_unknown_task(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post(f"/api/v1/tasks/{uuid.uuid4()}/time-logs", headers=mock_admin_headers, json={"hours": 1})
    assert r.status_code == 404


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_task_endpoints_require_auth(client):
    t = uuid.uuid4()
    assert client.post("/api/v1/tasks", json={"title": "x"}).status_code == 401
    assert client.get("/api/v1/tasks").status_code == 401
    assert client.get(f"/api/v1/tasks/{t}").status_code == 401
    assert client.patch(f"/api/v1/tasks/{t}", json={}).status_code == 401
    assert client.delete(f"/api/v1/tasks/{t}").status_code == 401
    assert client.post(f"/api/v1/tasks/{t}/subtasks", json={"title": "x"}).status_code == 401
    assert client.patch(f"/api/v1/tasks/subtasks/{t}", json={}).status_code == 401
    assert client.delete(f"/api/v1/tasks/subtasks/{t}").status_code == 401
    assert client.post(f"/api/v1/tasks/{t}/comments", json={"content": "x"}).status_code == 401
    assert client.delete(f"/api/v1/tasks/comments/{t}").status_code == 401
    assert client.post(f"/api/v1/tasks/{t}/time-logs", json={"hours": 1}).status_code == 401
