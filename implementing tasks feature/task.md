# Tasks: Employee Task Tracking

- [x] **Phase 3: Nested Sub-resources**
  - [x] Implement subtask CRUD endpoints in `app/api/routers/tasks.py`
  - [x] Implement comment creation/deletion endpoints in `app/api/routers/tasks.py`
  - [x] Implement time log creation endpoint in `app/api/routers/tasks.py`
  - [x] Add unit tests for subtasks, comments, and time logs in `tests/test_tasks.py`

- [x] **Phase 4: Recurring Tasks Spawner**
  - [x] Create tasks scheduler in `app/modules/tasks/scheduler.py`
  - [x] Integrate tasks scheduler into app lifespan in `app/api/main.py`
  - [x] Add tests for spawning logic and intervals in `tests/test_tasks.py`

- [ ] **Phase 5: Task Notifications**
  - [ ] Create and apply migration `db/migrations/078_task_notification_templates.sql`
  - [ ] Implement `TaskNotificationService` in `app/modules/notifications/services/task_notifications.py`
  - [ ] Register delegate in `app/modules/notifications/services/notification_service.py`
  - [ ] Integrate notifications trigger calls in `app/modules/tasks/service.py`
  - [ ] Write notification delivery unit tests

- [ ] **Phase 6: Frontend Tasks Management**
  - [ ] Create Axios task API client and React Query hooks in UI codebase
  - [ ] Implement `/tasks` page, list view with status/priority filtering
  - [ ] Create detailed task view drawer with checklist, comments feed, and time logging
  - [ ] Implement modals for creating and editing tasks (Admin only)
  - [ ] Wire tasks route guards in router configuration

- [ ] **Phase 7: Reporting & Widgets**
  - [ ] Define backend reporting endpoints for task metrics
  - [ ] Build tasks dashboard widgets and completion metrics in UI
