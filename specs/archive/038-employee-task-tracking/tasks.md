# Tasks: Employee Task Tracking
# Spec: specs/038-employee-task-tracking/spec.md
# Plan: specs/038-employee-task-tracking/plan.md

---

## Backend (techno_data_ Copy)

- [x] **Phase 1: DB Schema & ORM Models**
  - [x] Create `db/schema/11_tables_tasks.sql` — tasks, task_subtasks, task_comments, task_time_logs
  - [x] Apply `db/migrations/077_create_tasks_tables.sql`
  - [x] Implement `app/modules/tasks/models/task.py` — Task, TaskSubtask, TaskComment, TaskTimeLog + enums

- [x] **Phase 2: Core CRUD**
  - [x] Implement `app/modules/tasks/schemas.py` — CreateTaskInput, UpdateTaskInput, TaskReadDTO, TaskDetailDTO
  - [x] Implement `app/modules/tasks/interface.py` — TaskServiceInterface Protocol
  - [x] Implement `app/modules/tasks/repository.py` — TasksUnitOfWork + TaskRepository
  - [x] Implement `app/modules/tasks/service.py` — TaskService (create, list, get, update, soft_delete)
  - [x] Implement `app/api/routers/tasks.py` — CRUD endpoints
  - [x] Register router in `app/api/main.py`
  - [x] Add `get_task_service` to `app/api/dependencies.py`

- [x] **Phase 3: Nested Sub-resources**
  - [x] Implement subtask CRUD endpoints (`POST /tasks/{id}/subtasks`, `PATCH /subtasks/{id}`, `DELETE /subtasks/{id}`)
  - [x] Implement comment create/delete endpoints (`POST /tasks/{id}/comments`, `DELETE /comments/{id}`)
  - [x] Implement time log create endpoint (`POST /tasks/{id}/time-logs`)
  - [x] Add unit tests: subtask lifecycle, comment lifecycle, time log success

- [x] **Phase 4: Recurring Tasks Spawner**
  - [x] Create `app/modules/tasks/scheduler.py` — APScheduler daily job calling `spawn_recurring_tasks`
  - [x] Implement `TaskService.spawn_recurring_tasks(target_date)` — pattern matching + duplicate guard + child creation + subtask clone
  - [x] Integrate scheduler into `app/api/main.py` lifespan
  - [x] Add tests: daily/weekly/monthly/custom_interval spawning + no-duplicate guard

- [x] **Phase 5: Task Notifications**
  - [x] Apply `db/migrations/078_task_notification_templates.sql` — seed 4 email templates (task_assigned, task_status_changed, task_comment_added, task_due_reminder)
  - [x] Implement `app/modules/notifications/services/task_notifications.py` — TaskNotificationService (4 async processors)
  - [x] Fix wrong import: `app.modules.users` → `app.modules.auth.models.auth_models` in all 3 processors
  - [x] Register `self.task = TaskNotificationService(repo)` in `notification_service.py`
  - [x] Wire `notification_svc` into `get_task_service` in `dependencies.py`
  - [x] Add `BackgroundTasks` injection to `create_task`, `update_task`, `add_comment` endpoints in router
  - [x] Pass `background_tasks` kwarg from router → service methods
  - [x] All 11 tests in `tests/test_tasks.py` green ✅

---

## Frontend (techno_terminal_UI)

- [x] **Phase 6: Frontend Tasks Management**
  - [x] **6.1 API Client**
    - [x] Create `src/api/tasks/types.ts` — TaskReadDTO, TaskDetailDTO, TaskSubtaskReadDTO, TaskCommentReadDTO, TaskTimeLogReadDTO, CreateTaskInput, UpdateTaskInput, TaskFilters
    - [x] Create `src/api/tasks/tasks.ts` — getTasks, getTask, createTask, updateTask, deleteTask, addSubtask, updateSubtask, deleteSubtask, addComment, deleteComment, addTimeLog
    - [x] Export from `src/api/tasks/index.ts`
  - [x] **6.2 React Query Hooks**
    - [x] Add task query key factories to `src/hooks/queryKeys.ts`
    - [x] Create `src/hooks/useTasks.ts` — useTaskList, useTaskDetail, useCreateTask, useUpdateTask, useDeleteTask, useAddSubtask, useToggleSubtask, useAddComment, useDeleteComment, useAddTimeLog
  - [x] **6.3 Components**
    - [x] `src/components/tasks/TaskStatusBadge.tsx` — color-coded status chip (todo/in_progress/done/cancelled)
    - [x] `src/components/tasks/TaskPriorityBadge.tsx` — priority badge (low/medium/high/urgent)
    - [x] `src/components/tasks/TaskListTable.tsx` — sortable table with status, priority, assignee, due date columns
    - [x] `src/components/tasks/TaskDetailDrawer.tsx` — side drawer with Overview / Subtasks / Activity tabs
    - [x] `src/components/tasks/CreateTaskModal.tsx` — admin-only create/edit modal (title, desc, priority, due date, assignee, recurring options)
    - [x] `src/components/tasks/SubtaskChecklist.tsx` — checklist with toggle (employee can toggle is_done)
    - [x] `src/components/tasks/CommentsFeed.tsx` — comment list + add comment form
    - [x] `src/components/tasks/TimeLogPanel.tsx` — time log list + log hours form
  - [x] **6.4 Page & Route**
    - [x] Create `src/pages/TasksPage.tsx` — top bar + filter bar + TaskListTable
    - [x] Add lazy-loaded route `/tasks` to `src/App.tsx`
    - [x] Wire `InstructorBlockedRoute` guard (or role-based hide of admin actions)
    - [x] Add "Tasks" link to sidebar (`src/components/layout/Sidebar.tsx`) and BottomNav
  - [x] **6.5 Build Validation**
    - [x] `npm run build` must pass (tsc-b clean)
    - [x] `npm run lint` must pass (ESLint flat config)

---

## Reporting (techno_data_ Copy — backend)

- [ ] **Phase 7: Reporting & Widgets**
  - [ ] **7.1 Reporting Endpoint**
    - [ ] Add `GET /api/v1/reports/tasks` — returns task metrics per employee (total, done, in_progress, overdue, total_hours_logged); query params: `assigned_to?`, `date_from?`, `date_to?`, `group_by=employee|date`
    - [ ] Add service method `TaskReportService.get_task_metrics(...)` in `app/modules/tasks/service.py` or new `report_service.py`
    - [ ] Register reporting endpoint in router
  - [ ] **7.2 Due Reminder Scheduler**
    - [ ] Extend `app/modules/tasks/scheduler.py` with a daily 8:00 AM UTC job that queries tasks due ≤ tomorrow (status ≠ done/cancelled) and calls `notify_task_due_reminder` for each
  - [ ] **7.3 Frontend Dashboard Widget**
    - [ ] Create `src/components/tasks/TasksSummaryWidget.tsx` — open tasks count, overdue count, done this week
    - [ ] Integrate widget into admin dashboard page
