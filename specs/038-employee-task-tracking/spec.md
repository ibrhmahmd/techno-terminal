# Feature Specification: Employee Task Tracking

**Feature Branch**: `038-employee-task-tracking`  
**Created**: 2026-07-11  
**Status**: In Progress (Backend ✅ | Frontend ✅ | Reporting ⬜)  
**Input**: User description: "Employee task management system for STEM education center — create, assign, track, and report on employee tasks with subtasks, comments, time logging, recurring task spawning, and email notifications."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Admin Creates and Assigns a Task (Priority: P1)

An admin creates a new task (e.g., "Prepare STEM competition materials"), fills in title, description, priority, due date, and assigns it to an instructor. The assigned instructor immediately receives an email notification.

**Why this priority**: Core capability — everything else (subtasks, comments, time logs) hangs off task creation.

**Independent Test**: Create a task via `POST /api/v1/tasks`, verify it appears in `GET /api/v1/tasks`, and inspect notification log for the "task_assigned" template.

**Acceptance Scenarios**:

1. **Given** an admin is authenticated, **When** they `POST /api/v1/tasks` with valid payload including `assigned_to`, **Then** a `TaskDetailDTO` is returned, task is persisted, and a background email is queued to the employee.
2. **Given** a non-admin employee tries to create a task, **When** they call `POST /api/v1/tasks`, **Then** a `401 AuthError` is returned.
3. **Given** an `assigned_to` ID for a non-existent employee, **When** the task is created, **Then** a `404 NotFoundError` is returned.

---

### User Story 2 — Employee Updates Task Status (Priority: P1)

An assigned instructor marks their task as "in_progress" then "done". Admin and assigned employee both receive a status-change notification email. The admin sees the updated status in the task list.

**Why this priority**: Core workflow — task lifecycle tracking is the primary value of the feature.

**Independent Test**: `PATCH /api/v1/tasks/{id}` with `{"status": "done"}` from employee token, assert 200 + notification log entry for "task_status_changed".

**Acceptance Scenarios**:

1. **Given** an assigned employee, **When** they `PATCH /api/v1/tasks/{id}` with only `{"status": "in_progress"}`, **Then** status updates and a notification fires.
2. **Given** an assigned employee, **When** they try to update `title` or `priority`, **Then** a `401 AuthError` is returned (employees are status-only).
3. **Given** an unassigned employee, **When** they try to update any field, **Then** a `401 AuthError` is returned.

---

### User Story 3 — Subtask Checklist (Priority: P2)

An admin breaks a task into subtasks ("Design slide deck", "Review content", "Print materials"). An assigned employee checks off subtasks one by one. Admin can see completion percentage in the task detail view.

**Why this priority**: Granular progress tracking within a task — key for larger tasks.

**Independent Test**: `POST /api/v1/tasks/{id}/subtasks`, then `PATCH /api/v1/tasks/subtasks/{sub_id}` with `{"is_done": true}` — verify both admin and employee flows.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they `POST /api/v1/tasks/{id}/subtasks` with `{"title": "Design slide deck"}`, **Then** a `TaskSubtaskReadDTO` is returned with `is_done: false`.
2. **Given** the assigned employee, **When** they `PATCH /tasks/subtasks/{id}` with `{"is_done": true}`, **Then** subtask updates successfully.
3. **Given** an employee on a different task, **When** they attempt to update this subtask, **Then** a `401 AuthError` is returned.

---

### User Story 4 — Comments & Collaboration (Priority: P2)

An admin adds a comment asking for an update. The assigned employee receives an email notification ("New comment on your task"). The employee replies. Either party can delete their own comment.

**Why this priority**: Communication thread tied to the task — reduces context-switching to external tools.

**Independent Test**: `POST /api/v1/tasks/{id}/comments`, verify comment persisted, then `DELETE /api/v1/tasks/comments/{id}` from author.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they `POST /tasks/{id}/comments`, **Then** a `TaskCommentReadDTO` is returned with `author_name` populated and email notification queued.
2. **Given** a non-author employee, **When** they `DELETE /tasks/comments/{id}`, **Then** a `401 AuthError` is returned.
3. **Given** a comment by an employee on their own task, **When** the same employee deletes it, **Then** it succeeds.

---

### User Story 5 — Time Logging (Priority: P2)

An assigned instructor logs 3 hours spent on a task with an optional note. Admins can see total hours logged per task in the detail view.

**Why this priority**: Hours tracking enables future cost/efficiency reporting.

**Independent Test**: `POST /api/v1/tasks/{id}/time-logs` with `{"hours": 3.0, "note": "Research phase"}` — verify total hours reflected in `TaskDetailDTO`.

**Acceptance Scenarios**:

1. **Given** the assigned employee, **When** they `POST /tasks/{id}/time-logs` with `hours > 0`, **Then** log is created and returned as `TaskTimeLogReadDTO`.
2. **Given** an unassigned employee, **When** they attempt to log time, **Then** a `401 AuthError` is returned.

---

### User Story 6 — Recurring Tasks Automatic Spawning (Priority: P3)

An admin creates a "Weekly class preparation" task as a recurring task with `recurrence_pattern: "weekly"` and `recurrence_day_of_week: 1` (Monday). Every Monday the scheduler automatically spawns a child task copying the template's title, priority, and subtasks.

**Why this priority**: Eliminates manual re-creation of routine tasks — high admin value once core CRUD is stable.

**Independent Test**: Call `TaskService.spawn_recurring_tasks(target_date=next_monday)` directly, assert one child task created with `parent_task_id` set and subtasks cloned.

**Acceptance Scenarios**:

1. **Given** a weekly recurring task template, **When** `spawn_recurring_tasks` is called with the correct weekday, **Then** one child task is created with subtasks cloned and `is_recurring: false`.
2. **Given** the scheduler already spawned a task today, **When** `spawn_recurring_tasks` is called again for the same date, **Then** no duplicate is created.
3. **Given** a `custom_interval` recurring task with `recurrence_interval_days: 7`, **When** 7+ days have passed since last child, **Then** a new child is spawned.

---

### User Story 7 — Frontend Task Management Page (Priority: P3)

An admin opens the `/tasks` page in the web UI, sees all tasks in a filterable list (by status, priority, assignee). They create a new task from a modal, and see it appear instantly. An employee opening `/tasks` sees only a filtered list of their assigned tasks in practice (backend enforces read-all but UI scopes by role).

**Why this priority**: The backend is complete — the UI is the remaining delivery gate for end-users.

**Independent Test**: Navigate to `/tasks`, verify task list renders, create task from modal, assert it appears in the list without full-page reload.

**Acceptance Scenarios**:

1. **Given** an admin user, **When** they visit `/tasks`, **Then** all tasks are listed with status chips and priority badges.
2. **Given** an admin, **When** they click "New Task" and fill the form, **Then** task is created via API and appears in the list.
3. **Given** they click a task row, **When** the detail drawer opens, **Then** subtasks, comments, and time logs are displayed.
4. **Given** an employee user, **When** they open a task detail, **Then** they can update the status but the edit fields for title/priority are disabled.

---

### User Story 8 — Reporting & Dashboard Widgets (Priority: P4)

Admins see a tasks summary widget on the dashboard: total open tasks, overdue tasks, tasks by assignee. A `/reports/tasks` endpoint returns task completion metrics (total, done, in-progress, overdue) grouped by employee or date range.

**Why this priority**: Provides actionable insight after the core CRUD + UI are in place.

**Independent Test**: `GET /api/v1/reports/tasks?group_by=employee` returns at least `{ employee_id, task_count, completed, overdue }` per employee.

**Acceptance Scenarios**:

1. **Given** tasks in various statuses exist, **When** `GET /reports/tasks` is called, **Then** summary includes `total`, `done`, `in_progress`, `overdue` counts.
2. **Given** filtering by `assigned_to`, **When** the query is applied, **Then** only that employee's metrics are returned.

---

### Edge Cases

- What happens when a task's `due_date` passes without status change? → `notify_task_due_reminder` is called by a scheduler (not yet implemented); overdue tasks remain visible in the list with a "Overdue" indicator.
- What if an employee's account is deactivated after task assignment? → The task remains assigned; notifications silently skip if no email is found on the employee record.
- What if `recurrence_interval_days` is `None` for a `custom_interval` task? → The spawner skips this template (no crash, just a no-op).
- What if `spawn_recurring_tasks` is invoked more than once on the same day? → The duplicate-detection check (`Task.created_at` range for that date) prevents double-spawning.
- What if `assigned_to` is `None` (unassigned) and a status-change notification fires? → The notification is sent only to admin recipients (employee branch is skipped).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST restrict task creation and hard deletion to `admin`/`system_admin` roles.
- **FR-002**: Assigned employees MUST be able to update only the `status` field; all other fields require admin.
- **FR-003**: Employees MUST only be able to comment on and log time to tasks assigned directly to them.
- **FR-004**: System MUST prevent double-spawning of recurring child tasks for the same parent on the same calendar day.
- **FR-005**: Recurring task templates MUST support four patterns: `daily`, `weekly`, `monthly`, `custom_interval`.
- **FR-006**: Email notifications MUST be dispatched asynchronously via `BackgroundTasks` for: task assigned, status changed, comment added.
- **FR-007**: All task mutations MUST be soft-deleted (`deleted_at` timestamp), never hard-deleted.
- **FR-008**: Task detail response MUST include nested subtasks, comments, and time_logs in a single `TaskDetailDTO`.
- **FR-009**: Frontend task list MUST support filtering by `status`, `priority`, `assigned_to`, and `is_recurring`.
- **FR-010**: Reporting endpoint MUST expose task metrics (total, done, in_progress, overdue) queryable by employee and date range.

### Key Entities

- **Task**: Core entity. Fields: `title`, `description`, `due_date`, `priority`, `status`, `assigned_to` (FK→Employee), `assigned_by` (FK→User), `estimated_hours`, `tags`, `is_recurring`, `recurrence_pattern`, `recurrence_interval_days`, `recurrence_day_of_week`, `recurrence_day_of_month`, `parent_task_id` (self-ref FK), `deleted_at`.
- **TaskSubtask**: Checklist item under a task. Fields: `task_id`, `title`, `is_done`.
- **TaskComment**: Discussion thread entry. Fields: `task_id`, `author_id` (FK→User), `content`.
- **TaskTimeLog**: Hours tracking entry. Fields: `task_id`, `employee_id`, `hours`, `note`, `logged_at`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 11 backend tests in `tests/test_tasks.py` pass (Phases 3–5 complete).
- **SC-002**: Task creation + assignment email reaches the employee's inbox within 5 seconds of the API response.
- **SC-003**: Recurring tasks scheduler spawns the correct child task within 1 minute of midnight on the target date (no duplicate children).
- **SC-004**: Frontend `/tasks` page loads task list in under 2 seconds on a cold cache with up to 500 tasks.
- **SC-005**: Reporting endpoint returns task metrics in under 500 ms for up to 1000 tasks.

---

## Assumptions

- All employees have valid email addresses stored in `employees.email`; employees without email silently skip notifications.
- The frontend runs against the same Supabase auth — employee role detection uses JWT `app_metadata.role`.
- Part-time and contract instructors are treated identically in task access; employment type does not gate task visibility.
- The recurring tasks scheduler fires once per day at midnight UTC (wired into FastAPI's `lifespan` event via `apscheduler`).
- Phase 6 (frontend) and Phase 7 (reporting) are implemented in the `techno_terminal_UI` repo (`e:\Users\ibrahim\Desktop\techno_terminal_UI`).
- The "due reminder" notification (`task_due_reminder`) is wired but the scheduler that calls it daily is deferred to Phase 7.
