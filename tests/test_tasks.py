"""
Test module for Tasks router.
"""
import pytest
import uuid


class TestTasksCRUD:
    """Tests CRUD endpoints for tasks:
    - POST /api/v1/tasks
    - GET /api/v1/tasks
    - GET /api/v1/tasks/{id}
    - PATCH /api/v1/tasks/{id}
    - DELETE /api/v1/tasks/{id}
    """

    def test_create_task_admin_success(self, client, mock_admin_headers, override_auth):
        """POST /tasks creates task when admin."""
        task_data = {
            "title": "Clean the Lego Robotics Lab",
            "description": "Ensure EV3 and Spike kits are back in their boxes.",
            "due_date": "2026-07-20",
            "priority": "high",
            "status": "todo",
            "tags": ["Lego", "Lab"]
        }
        response = client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == task_data["title"]
        assert data["data"]["priority"] == "high"
        assert data["data"]["status"] == "todo"
        assert "id" in data["data"]

    def test_create_task_unauthorized(self, client):
        """POST /tasks without auth returns 401."""
        response = client.post("/api/v1/tasks", json={"title": "Unauthorized task"})
        assert response.status_code == 401

    def test_list_tasks(self, client, mock_admin_headers, override_auth):
        """GET /tasks returns list of tasks."""
        # Create a task first
        client.post(
            "/api/v1/tasks",
            json={"title": "List task test"},
            headers=mock_admin_headers
        )

        response = client.get("/api/v1/tasks", headers=mock_admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_get_task_by_id(self, client, mock_admin_headers, override_auth):
        """GET /tasks/{id} returns details."""
        # Create task
        create_resp = client.post(
            "/api/v1/tasks",
            json={"title": "Single task"},
            headers=mock_admin_headers
        )
        task_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/tasks/{task_id}", headers=mock_admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == task_id
        assert data["data"]["title"] == "Single task"

    def test_get_task_not_found(self, client, mock_admin_headers, override_auth):
        """GET /tasks/{id} returns 404 if not found."""
        random_uuid = str(uuid.uuid4())
        response = client.get(f"/api/v1/tasks/{random_uuid}", headers=mock_admin_headers)
        assert response.status_code == 404
        assert response.json()["success"] is False
        assert response.json()["error"] == "NotFoundError"

    def test_update_task_admin_success(self, client, mock_admin_headers, override_auth):
        """PATCH /tasks/{id} allows full updates for admins."""
        # Create task
        create_resp = client.post(
            "/api/v1/tasks",
            json={"title": "Update task admin", "priority": "low"},
            headers=mock_admin_headers
        )
        task_id = create_resp.json()["data"]["id"]

        update_data = {
            "title": "Updated by admin",
            "priority": "urgent"
        }
        response = client.patch(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=mock_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated by admin"
        assert data["data"]["priority"] == "urgent"

    def test_soft_delete_admin(self, client, mock_admin_headers, override_auth):
        """DELETE /tasks/{id} soft deletes task."""
        # Create task
        create_resp = client.post(
            "/api/v1/tasks",
            json={"title": "To be deleted"},
            headers=mock_admin_headers
        )
        task_id = create_resp.json()["data"]["id"]

        # Delete it
        del_response = client.delete(f"/api/v1/tasks/{task_id}", headers=mock_admin_headers)
        assert del_response.status_code == 200
        assert del_response.json()["success"] is True

        # Try to fetch it - should be 404
        get_response = client.get(f"/api/v1/tasks/{task_id}", headers=mock_admin_headers)
        assert get_response.status_code == 404

    def test_subtask_lifecycle_admin(self, client, mock_admin_headers, override_auth):
        """POST, PATCH, DELETE for subtasks by admin."""
        # Create task
        task_resp = client.post(
            "/api/v1/tasks",
            json={"title": "Main Task"},
            headers=mock_admin_headers
        )
        task_id = task_resp.json()["data"]["id"]

        # Create subtask
        subtask_resp = client.post(
            f"/api/v1/tasks/{task_id}/subtasks",
            json={"title": "Checklist Item 1"},
            headers=mock_admin_headers
        )
        assert subtask_resp.status_code == 200
        sub_data = subtask_resp.json()["data"]
        assert sub_data["title"] == "Checklist Item 1"
        assert sub_data["is_done"] is False
        subtask_id = sub_data["id"]

        # Update subtask
        update_resp = client.patch(
            f"/api/v1/tasks/subtasks/{subtask_id}",
            json={"title": "Checklist Item 1 Updated", "is_done": True},
            headers=mock_admin_headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["is_done"] is True
        assert update_resp.json()["data"]["title"] == "Checklist Item 1 Updated"

        # Delete subtask
        del_resp = client.delete(
            f"/api/v1/tasks/subtasks/{subtask_id}",
            headers=mock_admin_headers
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

    def test_comment_lifecycle(self, client, mock_admin_headers, override_auth):
        """POST and DELETE comments."""
        # Create task
        task_resp = client.post(
            "/api/v1/tasks",
            json={"title": "Comment Task"},
            headers=mock_admin_headers
        )
        task_id = task_resp.json()["data"]["id"]

        # Add comment
        comment_resp = client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "This is a comment"},
            headers=mock_admin_headers
        )
        assert comment_resp.status_code == 200
        comment_data = comment_resp.json()["data"]
        assert comment_data["content"] == "This is a comment"
        assert comment_data["author_name"] == "test_admin"
        comment_id = comment_data["id"]

        # Delete comment
        del_resp = client.delete(
            f"/api/v1/tasks/comments/{comment_id}",
            headers=mock_admin_headers
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

    def test_time_log_success(self, client, app, db_session, mock_admin_headers, override_auth):
        """POST time-logs by assigned employee."""
        # Create an employee first
        from app.modules.hr.models.employee_models import Employee
        from app.modules.auth.models.auth_models import User as UserModel
        
        unique_suffix = str(uuid.uuid4().hex[:6])
        emp = Employee(
            full_name="Task Worker",
            phone=f"1234{unique_suffix}",
            national_id=f"12345678{unique_suffix}",
            university="Test Uni",
            major="Testing",
            employment_type="full_time",
            is_active=True
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)

        # Create a user linked to this employee
        user = UserModel(
            username=f"task_worker_{unique_suffix}",
            role="instructor",
            supabase_uid=f"test-worker-{unique_suffix}",
            employee_id=emp.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create task assigned to this employee
        task_resp = client.post(
            "/api/v1/tasks",
            json={"title": "Assigned Task", "assigned_to": emp.id},
            headers=mock_admin_headers
        )
        task_id = task_resp.json()["data"]["id"]

        # Override auth to log in as task_worker
        from app.api.dependencies import get_current_user
        async def mock_get_worker():
            return user
        app.dependency_overrides[get_current_user] = mock_get_worker

        try:
            # Log time
            log_resp = client.post(
                f"/api/v1/tasks/{task_id}/time-logs",
                json={"hours": 2.5, "note": "Worked on it"},
                headers={"Authorization": "Bearer some-token"}
            )
            assert log_resp.status_code == 200
            log_data = log_resp.json()["data"]
            assert log_data["hours"] == 2.5
            assert log_data["note"] == "Worked on it"
            assert log_data["employee_name"] == "Task Worker"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_recurring_tasks_spawning(self, client, app, db_session, mock_admin_headers, override_auth):
        """Test spawning child tasks from templates."""
        from datetime import date, timedelta
        from app.modules.tasks.models import Task, TaskSubtask
        from sqlmodel import select
        
        # 1. Create a daily recurring task
        task_data = {
            "title": "Daily Lego Lab cleanup",
            "description": "Sort the bricks.",
            "is_recurring": True,
            "recurrence_pattern": "daily",
            "due_date": "2026-07-15",
            "priority": "medium",
            "status": "todo"
        }
        create_resp = client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=mock_admin_headers
        )
        assert create_resp.status_code == 200
        parent_id = create_resp.json()["data"]["id"]
        
        # Add a subtask to this parent task
        sub_resp = client.post(
            f"/api/v1/tasks/{parent_id}/subtasks",
            json={"title": "Sort EV3 components"},
            headers=mock_admin_headers
        )
        assert sub_resp.status_code == 200
        
        # Get TaskService to run spawning
        from app.api.dependencies import get_task_service
        service = get_task_service(db_session)
        
        # Target date
        target_date = date(2026, 7, 16)
        
        # Run spawner - at least 1 spawned (our task; test DB may have other recurring tasks)
        spawned = service.spawn_recurring_tasks(target_date)
        assert spawned >= 1
        
        # Verify exactly one child for OUR parent was created
        child_stmt = select(Task).where(Task.parent_task_id == parent_id)
        children = db_session.exec(child_stmt).all()
        assert len(children) == 1
        child = children[0]
        assert child.title == "Daily Lego Lab cleanup"
        assert child.is_recurring is False
        
        parent_offset = (date(2026, 7, 15) - date.today()).days
        assert child.due_date is not None
        assert child.due_date == target_date + timedelta(days=max(0, parent_offset))
        
        # Verify subtask was cloned
        child_subs_stmt = select(TaskSubtask).where(TaskSubtask.task_id == child.id)
        child_subs = db_session.exec(child_subs_stmt).all()
        assert len(child_subs) == 1
        assert child_subs[0].title == "Sort EV3 components"
        assert child_subs[0].is_done is False
        
        # Idempotency: run spawner again on same date - our parent should NOT produce another child
        service.spawn_recurring_tasks(target_date)
        children_after = db_session.exec(child_stmt).all()
        assert len(children_after) == 1, "Spawner created a duplicate child for the same parent on the same date"


