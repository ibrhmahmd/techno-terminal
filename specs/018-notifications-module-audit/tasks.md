---

description: "Task list for Notifications Module Audit — 32 issues, 21 user stories, code-only fixes"
---

# Tasks: Notifications Module Audit

**Input**: Design documents from `/specs/018-notifications-module-audit/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested — run existing notification tests (15/15) after all phases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Most stories touch different files/methods, so parallel execution is the default.

---

## Format: `[ID] [P] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Single config field needed by 2 user stories

- [ ] T001 Add `fallback_email: str = "ibrahim.ahmd.net@gmail.com"` to `Settings` class in `app/core/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Helper methods that unblock US-002 (CompetitionNotificationService crashes)

- [ ] T002 [US11] Add `_get_student_name()`, `_get_group_name()`, `_get_instructor_name()` helper methods to `BaseNotificationService` in `app/modules/notifications/services/base_notification_service.py` — each queries `self._repo._session.get(Model)` and returns the name
- [ ] T003 [US11] Remove duplicated `_get_student_name()`, `_get_group_name()`, `_get_instructor_name()` from `EnrollmentNotificationService` in `app/modules/notifications/services/enrollment_notifications.py` — now inherited from `BaseNotificationService`

**Checkpoint**: Helpers moved. US-002 competition crashes are now implicitly fixed (helpers inherited).

---

## Phase 3: US-001 — Fix SQL injection in AdminSettingsRepository (P1)

**Goal**: Remove SQL injection vector by parameterizing all queries

**Independent Test**: Submit a request with `notification_type="'; DROP TABLE admin_settings; --"` — should parameterize safely, not crash the DB

- [ ] T004 [P] [US1] Convert `upsert_admin_settings`, `get_admin_settings`, `get_all_admin_settings` in `app/modules/notifications/repositories/admin_settings_repository.py` from f-string SQL to `text()` with `:param` placeholders
- [ ] T005 [P] [US1] Convert `get_additional_recipients`, `add_additional_recipient`, `remove_additional_recipient`, `update_additional_recipient` in `app/modules/notifications/repositories/admin_settings_repository.py` from f-string SQL to `text()` with `:param` placeholders

**Checkpoint**: No f-string SQL remains in AdminSettingsRepository. All user-controlled values are bound via `:param`.

---

## Phase 4: US-002 — CompetitionNotificationService crashes (P1)

**Goal**: `CompetitionNotificationService` no longer crashes at 3 call sites calling undefined methods

**Independent Test**: `CompetitionNotificationService.notify_team_registration()`, `.notify_fee_payment()`, `.notify_placement()` execute without `AttributeError`

**Note**: Already resolved by Phase 2 (helpers moved to `BaseNotificationService`). Verify only — no code change needed if inheritance chain is correct.

- [ ] T006 [US2] Verify `CompetitionNotificationService` in `app/modules/notifications/services/competition_notifications.py` has no remaining calls to undefined private helpers — confirm `_get_student_name`, `_get_group_name`, `_get_instructor_name` resolve via MRO to `BaseNotificationService`

---

## Phase 5: US-003 — Fix get_template_by_code (P1)

**Goal**: Remove method that queries non-existent model field

**Independent Test**: `get_template_by_code()` no longer exists (removed)

- [ ] T007 [US3] Remove `get_template_by_code(self, code: str)` method from `NotificationRepository` in `app/modules/notifications/repositories/notification_repository.py` — verify zero callers across codebase with grep before deleting

---

## Phase 6: US-007 — Fix commit vs flush (P2)

**Goal**: Consistent transaction patterns — AdminSettingsRepository uses `flush()` like NotificationRepository

**Independent Test**: AdminSettingsRepository write operations don't trigger unexpected commits

**Note**: Same file as US-001. Tasks can run in parallel since they touch different methods.

- [ ] T008 [P] [US7] Replace `self._session.commit()` with `self._session.flush()` in `upsert_admin_settings`, `add_additional_recipient`, `update_additional_recipient`, `remove_additional_recipient` in `app/modules/notifications/repositories/admin_settings_repository.py`

---

## Phase 7: US-009 — Fix datetime.utcnow() deprecations (P2)

**Goal**: No deprecated `datetime.utcnow()` calls in notifications module

**Independent Test**: Grep shows zero `datetime.utcnow` in notifications files

- [ ] T009 [P] [US9] Replace `default_factory=datetime.utcnow` with `default_factory=lambda: datetime.now(timezone.utc)` in `NotificationTemplate.updated_at` (`app/modules/notifications/models/notification_template.py:28`)
- [ ] T010 [P] [US9] Replace `default_factory=datetime.utcnow` with `default_factory=lambda: datetime.now(timezone.utc)` in `NotificationLog.created_at`, `NotificationLog.updated_at`, `NotificationLog.sent_at` (`app/modules/notifications/models/notification_log.py:25`)
- [ ] T011 [P] [US9] Replace `datetime.utcnow().isoformat()` with `datetime.now(timezone.utc).isoformat()` in `app/modules/notifications/services/base_notification_service.py`

---

## Phase 8: US-010 — Fix dispatcher Protocol inheritance (P2)

**Goal**: `isinstance()` checks on dispatchers work correctly via `@runtime_checkable`

**Independent Test**: `isinstance(GmailEmailDispatcher(), IMessageDispatcher)` returns `True`

- [ ] T012 [P] [US10] Add `(IMessageDispatcher)` base class to `GmailEmailDispatcher` in `app/modules/notifications/dispatchers/email_dispatcher.py` — add import `from app.modules.notifications.dispatchers.i_dispatcher import IMessageDispatcher`
- [ ] T013 [P] [US10] Add `(IMessageDispatcher)` base class to `TwilioWhatsAppDispatcher` in `app/modules/notifications/dispatchers/whatsapp_dispatcher.py` — add import

---

## Phase 9: US-012 + US-020 — Fix async task ref + intended_recipients_count (P2/P3)

**Goal**: Proper task management and accurate fallback context

- [ ] T014 [US12] Store `asyncio.create_task()` return value in `self._background_tasks` set in `app/modules/notifications/services/base_notification_service.py` line ~161 instead of calling `asyncio.create_task()` without storing a reference
- [ ] T015 [US20] Change `intended_recipients_count=0` to `intended_recipients_count=len(recipient_emails)` in `_resolve_notification_recipients` in `app/modules/notifications/services/base_notification_service.py`

---

## Phase 10: US-004 + US-006 — Remove dead code + Remove commented-out parent code (P2)

**Goal**: Zero deprecated shims, zero commented-out code, zero unused methods

**Independent Test**: Grep for `def notify_enrollment(self` in `notification_service.py` returns no matches. Grep for `PARENT CODE` comments returns no matches.

- [ ] T016 [P] [US4] Delete 6 deprecated backward-compat methods from `NotificationService` in `app/modules/notifications/services/notification_service.py`: `notify_enrollment`, `notify_payment_receipt`, `notify_level_progression`, `notify_enrollment_completed`, `notify_enrollment_dropped`, `notify_enrollment_transferred`
- [ ] T017 [P] [US4+US6] Delete 4 commented-out `# PARENT CODE PRESERVED` blocks from `app/modules/notifications/services/enrollment_notifications.py` (lines ~124-129, ~188-193, ~224-229, ~259-264)
- [ ] T018 [P] [US4] Remove `get_enabled_admins_for_notification` method from `AdminSettingsRepository` in `app/modules/notifications/repositories/admin_settings_repository.py` (dead code — always returns `[]`)
- [ ] T019 [P] [US4] Remove unused imports (`List`, `Optional`, `Tuple`) in `app/modules/notifications/services/payment_notifications.py`
- [ ] T020 [P] [US4] Remove duplicate import on line 23 of `app/modules/notifications/services/base_notification_service.py`

---

## Phase 11: US-005 — Fix architecture violations (P2)

**Goal**: No router accesses `._repo` or `._session` — all goes through service methods

**Independent Test**: Grep all routers in `app/api/routers/notifications/` for `._repo` and `._session` — zero matches

- [ ] T021 [P] [US5] Add `get_all_templates()`, `get_template_by_id()`, `create_template()`, `update_template()`, `delete_template()` public methods to `NotificationService` in `app/modules/notifications/services/notification_service.py` — each delegates to `self._repo.<method>()`
- [ ] T022 [US5] Replace all `svc._repo.<method>()` calls with `svc.<method>()` in `app/api/routers/notifications/templates_router.py` — use the new facade methods from T021
- [ ] T023 [US5] Replace `svc._repo.get_logs()` with `svc.get_logs()` (or add `get_logs()` if missing) in `app/api/routers/notifications/notifications_router.py`
- [ ] T024 [US5] Fix `report_scheduler.py` in `app/modules/notifications/services/report_scheduler.py` — replace `svc._repo._session.close()` with a proper public close method or context manager
- [ ] T025 [P] [US5] Move `send_bulk` routing from `report` service to appropriate service in `app/modules/notifications/services/notification_service.py` (semantic mismatch)
- [ ] T026 [US5] Fix `test_and_send_template` to not access `self.report._dispatch` (private method) in `app/modules/notifications/services/notification_service.py`

---

## Phase 12: US-016 — Move lazy imports to module level (P3)

**Goal**: All imports at top of file

- [ ] T027 [US16] Move `TemplateTestResultDTO`, `get_session`, `AdminSettingsRepository` imports from inside method bodies to top of `app/modules/notifications/services/notification_service.py`

---

## Phase 13: US-017 — Fix MIME type split vulnerability (P3)

**Goal**: Safe string handling in MIME type parsing

- [ ] T028 [US17] Guard `mimetype.split("/", 1)` in `app/modules/notifications/dispatchers/email_dispatcher.py` line ~67 — check `"/" in mimetype` before splitting, or provide a sensible default

---

## Phase 14: US-018 — Lazy init Twilio client (P3)

**Goal**: App starts even if WhatsApp env vars are missing

- [ ] T029 [US18] Move `Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)` from `__init__` to lazy initialization in `_dispatch()` in `app/modules/notifications/dispatchers/whatsapp_dispatcher.py`

---

## Phase 15: US-013 — Type weekly/monthly aggregates (P3)

**Goal**: All repository methods return typed DTOs, not `dict`

- [ ] T030 [US13] Define `PeriodReportAggregateDTO(BaseModel)` with typed fields (`total_revenue: Decimal`, `total_sessions: int`, etc.) in `app/modules/notifications/services/report_notifications.py`
- [ ] T031 [US13] Update `_fetch_weekly_aggregates()` and `_fetch_monthly_aggregates()` return types in `app/modules/notifications/services/report_notifications.py` — replace `-> dict` with `-> PeriodReportAggregateDTO`

---

## Phase 16: US-014 — Typed bulk endpoint response (P3)

**Goal**: `response_model=ApiResponse[dict]` replaced with typed DTO

- [ ] T032 [US14] Create `BulkSendResultDTO(BaseModel)` with `queued_count: int` in appropriate schemas file
- [ ] T033 [US14] Change `response_model=ApiResponse[dict]` to `response_model=ApiResponse[BulkSendResultDTO]` in `app/api/routers/notifications/bulk_router.py`

---

## Phase 17: US-015 + US-019 — Scheduler kill-switch + traceback logging (P3)

**Goal**: Deployer can disable scheduler; tracebacks captured in logs

- [ ] T034 [US15] Add `scheduler_enabled: bool = True` to `Settings` class in `app/core/config.py`
- [ ] T035 [US15] Add `if not settings.scheduler_enabled: return` check at top of scheduler run loop in `app/modules/notifications/services/report_scheduler.py`
- [ ] T036 [US19] Replace `logger.error(f"...: {e}")` with `logger.exception("...")` in `app/modules/notifications/services/report_scheduler.py`

---

## Phase 18: US-021 — Remove duplicate model_dump call (P3)

**Goal**: No redundant operations

- [ ] T037 [US21] Remove duplicate `body.model_dump()` call in `app/api/routers/notifications/templates_router.py` line ~63 — call once, store result

---

## Phase 19: Polish & Verification

**Purpose**: Verify no regressions, all tests pass

- [ ] T038 Run `pytest tests/test_notifications.py -v -x` — diagnose and fix any failures
- [ ] T039 Run `pytest tests/ -v` — verify no regressions beyond notifications module

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 (config field not strictly required, but tidy)
- **US-001 (Phase 3)**: No dependencies — can run in parallel with Phases 2, 4
- **US-002 (Phase 4)**: Depends on Phase 2 (helpers must exist in BaseNotificationService)
- **US-003 (Phase 5)**: No dependencies
- **US-007 (Phase 6)**: No dependencies — same file as US-001, different methods, parallel safe
- **US-009 (Phase 7)**: No dependencies
- **US-010 (Phase 8)**: No dependencies
- **US-012+020 (Phase 9)**: No dependencies
- **US-004+006 (Phase 10)**: No dependencies (but removing shims before verifying callers could break callers — verify first)
- **US-005 (Phase 11)**: Depends on Phase 10 (needs NotificationService facade clean first for T021)
- **US-016 (Phase 12)**: No dependencies
- **US-017 (Phase 13)**: No dependencies
- **US-018 (Phase 14)**: No dependencies
- **US-013 (Phase 15)**: No dependencies
- **US-014 (Phase 16)**: No dependencies
- **US-015+019 (Phase 17)**: Depends on Phase 1 (scheduler_enabled config field)
- **US-021 (Phase 18)**: Depends on Phase 11 (touches same file)

### User Story Dependencies

- **US-002 → US-011**: Must move helpers before competition service gets them
- **US-005 → US-004**: Facade methods go in clean service (remove shims first)
- **US-021 → US-005**: Same file (templates_router.py)
- **US-015 → US-008**: Scheduler kill-switch needs config field
- **All others**: Independent — can execute in any order or parallel

### Within Each User Story

- Most stories are single-file, single-method changes
- No tests required (not requested by spec)
- Verify with grep after deletion tasks (dead code removal)

### Parallel Opportunities

- ALL tasks marked [P] can run in parallel (different files or different methods in same file)
- Phases 3, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16 can ALL run in parallel
- Sequential constraints: 1→2→4, 1→17, 10→11→18

---

## Parallel Example: Phase 3 + Phase 6 + Phase 7 + Phase 8

```bash
# All independent P-tasks, different files:
Task: "Parameterize upsert_admin_settings/get_admin_settings/get_all_admin_settings in admin_settings_repository.py"  [US1]
Task: "Replace commit() with flush() in admin_settings_repository.py"  [US7]
Task: "Fix datetime.utcnow in notification_template.py"  [US9]
Task: "Add Protocol inheritance to GmailEmailDispatcher in email_dispatcher.py"  [US10]
```

---

## Implementation Strategy

### MVP Scope (Phase 3 + Phase 4 + Phase 5 — P1 Criticals)

1. Complete Phase 1: Setup (config field)
2. Complete Phase 2: Foundational (move helpers — unblocks Phase 4)
3. Complete Phase 3: US-001 (SQL injection fix — security critical)
4. Complete Phase 4: US-002 (competition crashes fix — verified via Phase 2)
5. Complete Phase 5: US-003 (remove broken method)
6. **STOP and VALIDATE**: Run notification tests

### Full Incremental Delivery

1. P1 Criticals (Phases 1–5): Security + runtime fixes
2. P2 High (Phases 6–10, 11): Consistency + architecture + dead code
3. P3 Medium (Phases 12–18): Low-risk polish items
4. Final: Run full test suite

---

## Notes

- [P] tasks = different files/methods, no dependencies
- [Story] label maps task to specific user story for traceability
- No tests requested by spec — verify with existing test suite
- Grep before each deletion task to confirm zero callers
- All changes are code-only — no migrations
- Commit after each phase or logical group
- Stop at any checkpoint to verify story independently
