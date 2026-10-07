# Implementation Plan: Employee Task Tracking

**Branch**: `038-employee-task-tracking` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/038-employee-task-tracking/spec.md`

---

## Summary

Full employee task tracking system for Techno Terminal STEM center. Covers backend task CRUD, subtask checklists, commenting, time logging, recurring task auto-spawning, and email notification delivery. Remaining work is the React frontend (`/tasks` page) and a reporting endpoint for task metrics.

---

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript + React 18 (frontend)  
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL, APScheduler (recurring tasks), Starlette BackgroundTasks (notifications)  
**Storage**: PostgreSQL via Supabase (project `srbppkcvrgioneitktdj`)  
**Testing**: pytest (backend) · Vitest + React Testing Library (frontend)  
**Target Platform**: Linux server (Leapcell/Railpack) + Vercel (frontend)  
**Project Type**: Web service (REST API) + React SPA  
**Performance Goals**: Task list response < 200ms p95 · Notification delivery < 5s  
**Constraints**: Auth via Supabase JWT; no hard deletes; BackgroundTasks for all emails  
**Scale/Scope**: ~20 employees, ~500 tasks in steady state

---

## Constitution Check

- ✅ **Router → Service → Repository separation** — `tasks.py` router is HTTP-only; `TaskService` owns all rules; `TaskRepository` (via UoW) is pure SQL.
- ✅ **Two-Layer Schema Rule** — `app/modules/tasks/schemas.py` holds all DTOs; router does NOT import `app.api.schemas.tasks.*`.
- ✅ **Typed Contracts** — `TaskService` returns `TaskDetailDTO` and `TaskReadDTO`, never raw dicts or tuples.
- ✅ **UoW-based DI** — `get_task_service` in `dependencies.py` yields a session-scoped `TaskService(TasksUnitOfWork(session), notification_svc)`.
- ✅ **Notification gets own session** — `TaskNotificationService` opens a separate `get_session()` inside each async processor (same pattern as enrollment/payment notifications).
- ✅ **No circular imports** — `TaskService` uses `TYPE_CHECKING` guard for `NotificationService` and `BackgroundTasks`.
- ✅ **Dead code policy** — no commented-out code or deprecated shims in any tasks file.

---

## Project Structure

### Documentation (this feature)

```text
specs/038-employee-task-tracking/
├── spec.md          ← User stories & requirements (this session output)
├── plan.md          ← This file
└── tasks.md         ← Phase-by-phase implementation checklist
```

### Source Code (repository root — backend)

```text
app/
├── api/
│   ├── routers/
│   │   └── tasks.py                     ✅ DONE — CRUD + subtask + comment + time-log endpoints
│   └── dependencies.py                  ✅ DONE — get_task_service() wired with notification injection
│
├── modules/
│   └── tasks/
│       ├── __init__.py                  ✅ DONE — public exports
│       ├── interface.py                 ✅ DONE — TaskServiceInterface Protocol
│       ├── service.py                   ✅ DONE — business logic + BackgroundTasks wiring
│       ├── repository.py                ✅ DONE — UoW + query layer
│       ├── scheduler.py                 ✅ DONE — APScheduler recurring task spawner
│       ├── schemas.py                   ✅ DONE — all input/output DTOs
│       └── models/
│           └── task.py                  ✅ DONE — Task, TaskSubtask, TaskComment, TaskTimeLog
│
├── modules/notifications/services/
│   ├── task_notifications.py            ✅ DONE — TaskNotificationService (4 notification types)
│   └── notification_service.py         ✅ DONE — self.task delegate registered
│
db/
├── schema/
│   └── 11_tables_tasks.sql              ✅ DONE — all 4 task tables + indexes
└── migrations/
    ├── 077_create_tasks_tables.sql      ✅ DONE — initial schema
    └── 078_task_notification_templates.sql  ✅ DONE — 4 email templates seeded

tests/
└── test_tasks.py                        ✅ DONE — 11 tests, all passing
```

### Source Code (frontend — techno_terminal_UI)

```text
src/
├── api/
│   └── tasks/
│       ├── tasks.ts                     ✅ DONE — Axios client (CRUD + subtasks + comments + time-logs)
│       └── types.ts                     ✅ DONE — TaskDTO, TaskDetailDTO, filter params
│
├── hooks/
│   └── useTasks.ts                      ✅ DONE — React Query hooks (list, detail, mutations)
│
├── pages/
│   └── TasksPage.tsx                    ✅ DONE — list view with filters + create modal
│
├── components/tasks/
│   ├── TaskListTable.tsx                ✅ DONE — sortable/filterable task table
│   ├── TaskDetailDrawer.tsx             ✅ DONE — detail panel (subtasks checklist, comments, time-logs)
│   ├── CreateTaskModal.tsx              ✅ DONE — admin create/edit modal
│   ├── TaskStatusBadge.tsx             ✅ DONE — color-coded status chip
│   ├── TaskPriorityBadge.tsx           ✅ DONE — priority badge
│   ├── SubtaskChecklist.tsx            ✅ DONE — checklist with toggle
│   ├── CommentsFeed.tsx                ✅ DONE — comment list + add form
│   └── TimeLogPanel.tsx                ✅ DONE — time log list + log form
│
└── App.tsx                              ✅ DONE — lazy-loaded /tasks route with InstructorBlockedRoute
```

---

## Phase Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | DB schema + ORM models | ✅ Complete |
| 2 | Core CRUD (router + service + repository) | ✅ Complete |
| 3 | Nested sub-resources (subtasks, comments, time logs) | ✅ Complete |
| 4 | Recurring tasks scheduler | ✅ Complete |
| 5 | Task email notifications | ✅ Complete |
| 6 | Frontend `/tasks` page | ✅ Complete |
| 7 | Reporting endpoint + dashboard widget | ⬜ Pending |

---

## Phase 6 — Frontend Task Management (Next)

### 6.1 API Client (`src/api/tasks/`)

Create `tasks.ts` following the `src/api/crm/` pattern:

```ts
// Key functions to implement:
export const getTasks = (filters: TaskFilters) => api.get<PaginatedApiResponse<TaskReadDTO>>('/tasks', { params: filters })
export const getTask = (id: string) => api.get<ApiResponse<TaskDetailDTO>>(`/tasks/${id}`)
export const createTask = (dto: CreateTaskInput) => api.post<ApiResponse<TaskDetailDTO>>('/tasks', dto)
export const updateTask = (id: string, dto: UpdateTaskInput) => api.patch<ApiResponse<TaskDetailDTO>>(`/tasks/${id}`, dto)
export const deleteTask = (id: string) => api.delete<ApiResponse<boolean>>(`/tasks/${id}`)
// Subtasks, comments, time-logs follow same pattern
```

### 6.2 React Query Hooks (`src/hooks/useTasks.ts`)

Key query keys to register in `src/hooks/queryKeys.ts`:
```ts
tasks: {
  all: () => ['tasks'],
  list: (filters) => ['tasks', 'list', filters],
  detail: (id) => ['tasks', 'detail', id],
}
```

Mutations: `useCreateTask`, `useUpdateTask`, `useDeleteTask`, `useAddSubtask`, `useToggleSubtask`, `useAddComment`, `useDeleteComment`, `useAddTimeLog`.

### 6.3 Route Guard

Add to `App.tsx` lazy route list:
```tsx
<Route path="/tasks" element={
  <InstructorBlockedRoute>   {/* blocks role=instructor */}
    <Suspense fallback={<PageLoader />}>
      <TasksPage />
    </Suspense>
  </InstructorBlockedRoute>
} />
```

> **Note**: Employees (non-admin staff) CAN access `/tasks` — route guard blocks only `instructor` role if applicable. Admin-only actions (create, delete) are gated inside the page.

### 6.4 `TasksPage` Layout

- **Top bar**: "Tasks" heading + "New Task" button (admin only, hidden for employees)
- **Filter bar**: Status dropdown, Priority dropdown, Assignee dropdown, Recurring toggle
- **Task table**: columns — Title, Priority (badge), Status (chip), Assigned To, Due Date, Actions
- **Row click**: opens `TaskDetailDrawer`
- **`TaskDetailDrawer`**: 3 tabs — Overview (title/desc/meta) · Subtasks (checklist) · Activity (comments + time logs)

---

## Phase 7 — Reporting & Widgets (Deferred)

### 7.1 Backend Reporting Endpoint

```
GET /api/v1/reports/tasks
Query params: assigned_to?, date_from?, date_to?, group_by=employee|date
```

Response schema (per group):
```json
{
  "employee_id": 5,
  "employee_name": "Mariam Tawfik",
  "total": 12,
  "done": 8,
  "in_progress": 3,
  "overdue": 1,
  "total_hours_logged": 24.5
}
```

### 7.2 Due Reminder Scheduler

Wire a daily 8:00 AM job that calls `notify_task_due_reminder` for all tasks due within 1 day or already overdue (status ≠ done/cancelled).

### 7.3 Dashboard Widget

Add a `TasksSummaryWidget` to the admin dashboard alongside existing finance/enrollment widgets.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Self-referencing FK (`parent_task_id`) | Recurring tasks spawn children that point to their template | Separate "template" table adds schema complexity without benefit at this scale |
| `TYPE_CHECKING` guard in `service.py` | Breaks circular import (`NotificationService` → `TaskService`) | Cannot restructure without violating constitution import chain |
