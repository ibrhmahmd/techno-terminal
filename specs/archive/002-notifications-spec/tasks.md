# Tasks: Notifications Module

**Input**: Design documents from `/specs/002-notifications-spec/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Fix existing infrastructure issues that block all notification work

**No user story can begin until this phase is complete**

- [ ] T001 Remove bulk notification router in `app/api/routers/notifications/bulk_router.py` (delete file and remove its registration from `app/api/routers/notifications/__init__.py`)
- [ ] T002 [P] Add explicit `WHATSAPP_ENABLED` env var check in `app/modules/notifications/services/base_notification_service.py` line 278, replacing the silent-skip pattern
- [ ] T003 [P] Create DB migration `db/migrations/050_add_notification_retry_columns.sql` adding `retry_count INT DEFAULT 0` and `next_retry_at TIMESTAMP` to `notification_logs`
- [ ] T004 Create `MockEmailDispatcher` test fixture in `tests/utils/notification_mocks.py` that captures sent emails in-memory for assertion
- [ ] T005 Create `MockNotificationRepository` test fixture in `tests/utils/notification_mocks.py` for isolated testing of notification services

**Checkpoint**: Foundation ready — dead code removed, DB has retry columns, test mocks available.

---

## Phase 2: Cross-Cutting (Affects All Notification Types)

**Purpose**: Implement features shared across all notification types — retry logic, manual retry endpoint, and fix existing violations

- [ ] T006 [P] Refactor `app/modules/notifications/repositories/admin_settings_repository.py` — convert all `text(f"...WHERE admin_id = {admin_id}")` to parameterized queries using `text("...WHERE admin_id = :admin_id").bindparams(admin_id=admin_id)` (10+ methods)
- [ ] T007 [P] Update `app/modules/notifications/repositories/admin_settings_repository.py` return types from `list[dict]` to typed Pydantic DTOs (`AdminSettingDTO`, `AdditionalRecipientDTO` from `app/modules/notifications/schemas/admin_settings_dto.py`)
- [ ] T008 [P] Add retry fields to `NotificationLogDTO` in `app/modules/notifications/schemas/notification_dto.py` — add `retry_count: int = 0`, `next_retry_at: datetime | None`
- [ ] T009 [P] Add `RetryRequest` and `RetryResult` DTOs in `app/modules/notifications/schemas/send_request.py`
- [ ] T010 Implement retry logic in `app/modules/notifications/services/base_notification_service.py` — on dispatch failure, increment `retry_count`, calculate `next_retry_at` (1min/5min/30min by attempt), set status `RETRYING`, and add `_process_retry_queue()` polling method
- [ ] T011 Add manual retry endpoint `POST /api/v1/notifications/logs/{log_id}/retry` in `app/api/routers/notifications/notifications_router.py` — validate status is FAILED, reset to PENDING, re-dispatch, return `RetryResult`

**Checkpoint**: Cross-cutting features complete — retry works, manual retry endpoint available, repository uses safe queries with typed returns.

---

## Phase 3: User Story 1 — Enrollment Notifications (Priority: P1) 🎯 MVP

**Goal**: Admin receives email notifications when students are enrolled, complete levels, drop out, or transfer between groups.

**Independent Test**: Create an enrollment and verify a notification email is dispatched to configured recipients with correct student name, group name, and level data.

### Implementation for User Story 1

- [ ] T012 [US1] Write tests for enrollment notification events in `tests/test_notifications.py` — class `TestEnrollmentNotifications` covering enrollment_created, level_progression, enrollment_completed, enrollment_dropped, enrollment_transferred
- [ ] T013 [US1] Verify `EnrollmentNotificationService` in `app/modules/notifications/services/enrollment_notifications.py` correctly resolves template per event type and dispatches to subscribed recipients
- [ ] T014 [US1] Verify absence alert endpoint `POST /api/v1/notifications/absence` triggers correct enrollment notification flow

**Checkpoint**: Enrollment notifications independently testable and verified.

---

## Phase 4: User Story 2 — Payment Notifications (Priority: P1)

**Goal**: Admin receives email notifications when payments are received (with PDF receipt) and when payments are due.

**Independent Test**: Record a payment and verify a notification email with receipt number, amount, and PDF attachment is sent.

### Implementation for User Story 2

- [ ] T015 [US2] Write tests for payment notification events in `tests/test_notifications.py` — class `TestPaymentNotifications` covering payment_received (with PDF attachment) and payment_reminder
- [ ] T016 [US2] Verify `PaymentNotificationService` in `app/modules/notifications/services/payment_notifications.py` correctly generates PDF receipt attachment and dispatches to subscribed recipients
- [ ] T017 [US2] Verify receipt endpoint `POST /api/v1/notifications/receipt/{receipt_id}` triggers correct payment notification flow

**Checkpoint**: Payment notifications independently testable and verified.

---

## Phase 5: User Story 3 — Scheduled Business Reports (Priority: P2)

**Goal**: Center manager receives daily, weekly, and monthly business summary reports via email with PDF attachment.

**Independent Test**: Configure a report time, wait for scheduler trigger, and verify the report email is delivered with correct summary data.

### Implementation for User Story 3

- [ ] T018 [P] [US3] Write tests for daily report in `tests/test_notifications.py` — class `TestReportNotifications` test method `test_daily_report_sends`
- [ ] T019 [P] [US3] Write tests for weekly report — test method `test_weekly_report_sends`
- [ ] T020 [P] [US3] Write tests for monthly report — test method `test_monthly_report_sends`
- [ ] T021 [US3] Verify `ReportNotificationService` in `app/modules/notifications/services/report_notifications.py` correctly aggregates data and generates PDF via `daily_report_pdf.py`
- [ ] T022 [US3] Verify `report_scheduler.py` date-guard logic prevents duplicate sends on server restart

**Checkpoint**: Scheduled reports independently testable and verified.

---

## Phase 6: User Story 4 — Template Management (Priority: P2)

**Goal**: Admin creates, previews, tests, and updates notification email templates with variable placeholders. Standard templates are protected.

**Independent Test**: Create a template, preview it with placeholder substitutions, send a test email to recipients.

### Implementation for User Story 4

- [ ] T023 [P] [US4] Write tests for template CRUD in `tests/test_notifications.py` — class `TestTemplates` covering create, read, update, delete
- [ ] T024 [P] [US4] Write test for standard template immutability (name, variables, channel cannot change, deletion blocked)
- [ ] T025 [P] [US4] Write test for template test-send feature (`POST /templates/{id}/test`) verifying rendered output and recipient delivery
- [ ] T026 [US4] Verify `NotificationService.test_and_send_template()` in `app/modules/notifications/services/notification_service.py` correctly renders placeholders and dispatches

**Checkpoint**: Template management independently testable and verified.

---

## Phase 7: User Story 5 — Recipient Management (Priority: P2)

**Goal**: Admin manages email recipients and assigns them to specific notification types. Settings are toggled per type.

**Independent Test**: Add a recipient with notification type filters, trigger a matching event, verify the email is sent only to filtered recipients.

### Implementation for User Story 5

- [ ] T027 [P] [US5] Write tests for recipient CRUD in `tests/test_notifications.py` — class `TestRecipients` covering add, update, delete, toggle active
- [ ] T028 [P] [US5] Write tests for notification type filtering — class `TestRecipientFiltering` verifying recipients receive only their subscribed notification types
- [ ] T029 [P] [US5] Write tests for admin settings toggle (`PUT /admin/settings/me/types/{type}`) in `tests/test_notifications.py` — class `TestAdminSettings`
- [ ] T030 [US5] Verify `AdminSettingsRepository` in `app/modules/notifications/repositories/admin_settings_repository.py` returns typed DTOs after Phase 2 refactoring
- [ ] T031 [US5] Verify fallback mechanism in `BaseNotificationService._resolve_notification_recipients()` sends fallback alert when no recipients configured

**Checkpoint**: Recipient management independently testable and verified.

---

## Phase 8: User Story 6 — Competition Notifications (Priority: P3)

**Goal**: Admin receives notifications for competition team registration, fee payment, and placement announcements.

**Independent Test**: Register a team in a competition and verify a notification email with team name and competition details is sent.

### Implementation for User Story 6

- [ ] T032 [P] [US6] Write tests for competition notification events in `tests/test_notifications.py` — class `TestCompetitionNotifications` covering team_registration, fee_payment, placement
- [ ] T033 [US6] Verify `CompetitionNotificationService` in `app/modules/notifications/services/competition_notifications.py` correctly resolves templates per event type

**Checkpoint**: Competition notifications independently testable and verified.

---

## Phase 9: E2E Validation & Polish

**Purpose**: Final verification across all notification types

- [ ] T034 [P] Run full test suite: `pytest tests/ -v` — verify no regression from dead code removal or repository refactoring
- [ ] T035 Run notification-specific tests: `pytest tests/test_notifications.py -v` — verify all 6 user story test classes pass
- [ ] T036 Manual smoke test via Swagger UI at `http://localhost:8000/api/v1/docs` — verify notification endpoints return correct responses
- [ ] T037 Update `AGENTS.md` if needed — document any new notification module conventions discovered during implementation

**Checkpoint**: All notification types verified, full test suite green.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — MUST complete first
- **Phase 2 (Cross-Cutting)**: Depends on Phase 1 completion
- **Phases 3-8 (User Stories)**: Depends on Phase 1 and Phase 2 completion
  - User stories can proceed sequentially or P1 (US1, US2) → P2 (US3, US4, US5) → P3 (US6) in priority order
- **Phase 9 (E2E)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — can start after Phase 2
- **US2 (P1)**: No dependencies on other stories — can start after Phase 2
- **US3 (P2)**: No dependencies on other stories — can start after Phase 2
- **US4 (P2)**: No dependencies on other stories — can start after Phase 2
- **US5 (P2)**: Depends on AdminSettingsRepository refactoring (T006, T007 in Phase 2)
- **US6 (P3)**: No dependencies on other stories — can start after Phase 2

### Parallel Opportunities

- All [P] tasks within a phase can run in parallel
- US1, US2 can run in parallel (both P1, independent)
- US3, US4, US5 can run in parallel (all P2, independent after Phase 2 refactors)
- US6 can run alongside any P1 or P2 story

### Parallel Example

```bash
# Phase 2 parallel tasks:
Task: T006 Refactor AdminSettingsRepository
Task: T007 Update return types to DTOs
Task: T008 Add retry fields to NotificationLogDTO
Task: T009 Add RetryRequest/RetryResult DTOs

# User Stories (P1) parallel:
Task: T012 Write Enrollment notification tests
     + T013-T014 verify Enrollment notification flows
Task: T015 Write Payment notification tests
     + T016-T017 verify Payment notification flows
```

## Implementation Strategy

### MVP (Phase 1 + 2 + US1)
1. Complete Phase 1: Foundational
2. Complete Phase 2: Cross-Cutting
3. Complete Phase 3: User Story 1 (Enrollment Notifications)
4. **STOP and VALIDATE**: Run `pytest tests/test_notifications.py::TestEnrollmentNotifications -v`
5. Enrollment alerts working — deploy if ready

### Incremental Delivery
1. Phase 1 + 2 → Foundation + retry + refactoring complete
2. Add US1 (Enrollment) → Test independently → Deploy
3. Add US2 (Payment) → Test independently → Deploy
4. Add US3-5 (Reports, Templates, Recipients) → Test independently → Deploy
5. Add US6 (Competitions) → Test independently → Deploy

### Parallel Team Strategy
1. Phase 1 together
2. Phase 2: Split [P] tasks across developers
3. Phase 3-8: Assign stories independently after Phase 2
   - Dev A: US1 + US4 (Enrollment + Templates)
   - Dev B: US2 + US5 (Payment + Recipients)
   - Dev C: US3 + US6 (Reports + Competitions)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
