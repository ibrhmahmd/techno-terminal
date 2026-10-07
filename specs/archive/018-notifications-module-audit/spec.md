# Spec 018: Notifications Module Audit

**Created**: 2026-05-22 | **Status**: Draft
**Scope**: Full notifications module audit — 26 files, 7 service classes, 4 repositories, 4 dispatchers, 5 routers, 3 models

---

## Problem Statement

The notifications module was built incrementally across multiple spec cycles (002, 006, 012, 013, 017) without a holistic quality pass. A comprehensive audit of all 26 files revealed **32 issues** across 6 categories: 3 critical (security + runtime crashes), 7 high, 12 medium, and 10 low.

The module has:
- A **SQL injection vulnerability** in `AdminSettingsRepository` (all queries use f-string interpolation)
- **3 runtime crashes** in `CompetitionNotificationService` (calls undefined methods)
- **6 deprecated backward-compatibility shims** in `NotificationService` facade
- A **broken method** (`get_template_by_code`) that always returns `None`
- **Architecture violations** (routers accessing `._repo` directly, encapsulation breaches)
- **Inconsistent patterns** (`commit()` vs `flush()`, `os.getenv` vs Pydantic `settings`, deprecated `datetime.utcnow`)
- **Dead code** (commented-out blocks, unused import, defunct `get_enabled_admins_for_notification`)

---

## Success Criteria

1. All 3 critical issues resolved (SQL injection, CompetitionNotificationService crashes, `get_template_by_code`)
2. All deprecated shims removed, all dead code deleted
3. No router accesses `._repo` or `._session` directly — goes through service methods
4. All repositories use parameterized queries (no f-string SQL)
5. All `datetime.utcnow()` replaced with `datetime.now(timezone.utc)`
6. Weekly/monthly aggregates return typed DTOs
7. All notification tests pass (currently 15/15)
8. No regressions in enrollment, payment, or report notification workflows

---

## User Stories

### P1 — Must Fix (3 critical)

**US-001: Fix SQL injection in AdminSettingsRepository (Security)**
> As an admin, I want notification settings queries to be parameterized so that SQL injection is impossible.

All 8 query methods in `AdminSettingsRepository` use Python f-string interpolation with user-controlled values. `notification_type` comes from URL path params (`/{notification_type}`).

Files: `app/modules/notifications/repositories/admin_settings_repository.py` (all methods)

**US-002: Fix CompetitionNotificationService runtime crash**
> As a competition manager, I want to send team registration, fee payment, and placement notifications without getting an AttributeError.

`CompetitionNotificationService` calls `self._get_student_name(student_id)` at 3 call sites, but neither the class nor its parent `BaseNotificationService` defines this method. Only `EnrollmentNotificationService` defines it. Every notification dispatch crashes.

Files:
- `app/modules/notifications/services/competition_notifications.py:95,132,169`
- `app/modules/notifications/services/enrollment_notifications.py:268` (move `_get_student_name`, `_get_group_name`, `_get_instructor_name` to `BaseNotificationService`)

**US-003: Fix get_template_by_code broken method**
> As a developer, I want `get_template_by_code()` to return a template so that callers don't silently get None.

`NotificationRepository.get_template_by_code()` references `NotificationTemplate.code` which doesn't exist on the model. Always returns `None`.

File: `app/modules/notifications/repositories/notification_repository.py`

---

### P2 — Should Fix (7 high + 12 medium)

**US-004: Remove dead code (High)**
> As a maintainer, I want deprecated shims and dead code removed so the module is clean.

- Delete 6 deprecated backward-compat methods from `NotificationService` (`notify_enrollment`, `notify_payment_receipt`, `notify_level_progression`, `notify_enrollment_completed`, `notify_enrollment_dropped`, `notify_enrollment_transferred`)
- Delete 4 commented-out "PARENT CODE PRESERVED" blocks in `enrollment_notifications.py`
- Delete `get_enabled_admins_for_notification` (always returns `[]`, intentionally unused)
- Remove unused `List`, `Optional`, `Tuple` imports in `payment_notifications.py`
- Remove duplicate import in `base_notification_service.py` (line 23)

Files: `notification_service.py`, `enrollment_notifications.py`, `admin_settings_repository.py`, `payment_notifications.py`, `base_notification_service.py`

**US-005: Fix architecture violations (High)**
> As a developer, I want routers to go through service methods rather than accessing private attributes.

- `templates_router.py`: All CRUD operations access `svc._repo` directly — add service methods
- `notifications_router.py:47,58`: Accesses `svc._repo.get_logs()` directly
- `report_scheduler.py:52`: Accesses `svc._repo._session.close()` — add public close method
- `notification_service.py`: `send_bulk` routed through `report` service (semantic mismatch)
- `notification_service.py:267`: `test_and_send_template` accesses `self.report._dispatch` (private method)

Files: `templates_router.py`, `notifications_router.py`, `report_scheduler.py`, `notification_service.py`

**US-006: Remove commented-out parent code (High)**
> As a maintainer, I want no commented-out code in the codebase.

4 blocks of disabled parent notification code in `enrollment_notifications.py` (lines ~124-129, ~188-193, ~224-229, ~259-264).

File: `app/modules/notifications/services/enrollment_notifications.py`

**US-007: Fix inconsistent session patterns (Medium)**
> As a developer, I want consistent transaction patterns across the module.

- `AdminSettingsRepository` calls `self._session.commit()` — should use `flush()` like `NotificationRepository`
- `test_and_send_template` opens a separate session instead of using `self._repo._session`
- `report_scheduler` creates its own service factory closure instead of using DI

Files: `admin_settings_repository.py`, `notification_service.py`, `report_scheduler.py`

**US-008: Fix environment config pattern (Medium)**
> As a deployer, I want all config read from Pydantic settings, not os.getenv.

- `FALLBACK_EMAIL = os.getenv("FALLBACK_EMAIL", "ibrahim.ahmd.net@gmail.com")` in `base_notification_service.py`
- Should read from `app.core.config.settings`

File: `app/modules/notifications/services/base_notification_service.py:15`

**US-009: Fix datetime.utcnow() deprecations (Medium)**
> As a developer, I want no deprecated datetime calls.

3 occurrences:
- `notification_template.py:28` — `Field(default_factory=datetime.utcnow)`
- `notification_log.py:25` — `Field(default_factory=datetime.utcnow)`
- `base_notification_service.py:213` — `datetime.utcnow().isoformat()`

Files: notification model files + base service

**US-010: Fix dispatcher Protocol inheritance (Medium)**
> As a developer, I want dispatchers to formally implement their Protocol.

- `GmailEmailDispatcher` and `TwilioWhatsAppDispatcher` document "implements IMessageDispatcher" but don't inherit from it. `isinstance()` with `@runtime_checkable` will fail.

Files: `email_dispatcher.py`, `whatsapp_dispatcher.py`

**US-011: Move shared helpers to BaseNotificationService (Medium)**
> As a developer, I want shared helpers in one place, not duplicated.

- `_get_student_name`, `_get_group_name`, `_get_instructor_name` are defined only on `EnrollmentNotificationService` but needed by `CompetitionNotificationService`. Move to `BaseNotificationService`.
- Also resolves US-002 (the runtime crash).

Files: `enrollment_notifications.py`, `base_notification_service.py`, `competition_notifications.py`

**US-012: asyncio.create_task without task reference (Medium)**
> As a developer, I want async tasks managed properly to avoid pending task GC warnings.

`base_notification_service.py:161`: `asyncio.create_task(self._send_fallback_alert(context))` — no reference stored.

File: `base_notification_service.py`

---

### P3 — Nice to Fix (10 low)

**US-013: Type weekly/monthly aggregates (Low)**
> As a developer, I want all repository methods returning typed DTOs.

`_fetch_weekly_aggregates` and `_fetch_monthly_aggregates` return `dict`. Has `#TODO remove Dict` comment.

File: `report_notifications.py`

**US-014: Add typed response for bulk endpoint (Low)**
> As a developer, I want all API responses typed.

`bulk_router.py:11`: `response_model=ApiResponse[dict]` — should be a typed DTO with `queued_count: int`.

File: `bulk_router.py`

**US-015: Add SCHEDULER_ENABLED kill-switch (Low)**
> As a deployer, I want to disable the report scheduler without code changes.

No env var to disable the scheduler. Must add check at scheduler startup.

File: `report_scheduler.py`

**US-016: Move lazy imports to module level (Low)**
> As a developer, I want imports at the top of files.

`notification_service.py:168-170, 214-217`: Imports `TemplateTestResultDTO`, `get_session`, `AdminSettingsRepository` inside method bodies.

File: `notification_service.py`

**US-017: Fix MIME type split vulnerability (Low)**
> As a developer, I want safe string splitting.

`email_dispatcher.py:67`: `mimetype.split("/", 1)` will crash if `mimetype` has no `/`.

File: `email_dispatcher.py`

**US-018: Lazy init Twilio client (Low)**
> As a deployer, I want the app to start even if WhatsApp env vars are missing.

`whatsapp_dispatcher.py:__init__` eagerly creates `Client(...)` — fails at import time if env vars missing.

File: `whatsapp_dispatcher.py`

**US-019: Log traceback in scheduler exception (Low)**
> As a developer, I want full tracebacks in logs.

`report_scheduler.py:54`: `logger.error(f"...: {e}")` — should use `logger.exception()`.

File: `report_scheduler.py`

**US-020: Fix intended_recipients_count hardcode (Low)**
> As a developer, I want accurate fallback alert context.

`base_notification_service.py:157`: `intended_recipients_count=0` should reflect actual invalid count.

File: `base_notification_service.py`

**US-021: Remove duplicate model_dump in templates_router (Low)**
> As a developer, I want no redundant operations.

`templates_router.py:63`: `body.model_dump()` called twice with same parameters.

File: `templates_router.py`

---

## Scope

**In scope**: All 26 files within the notifications module, its API routers, and its test utilities. Cross-module callers (finance, enrollments) are in scope only for updating import paths if methods are renamed.

**Out of scope**: 
- Replacing `AdminSettingsRepository` with SQLModel models (would require migration)
- Adding new notification types
- Enabling WhatsApp dispatcher
- Refactoring the scheduler to persist `last_sent` (already documented in spec 012)

---

## Dependencies

- spec 012 (`012-scheduled-report-audit`) — documents the scheduler and its known issues
- spec 017 (`017-fix-report-critical-bugs`) — also touches `reports_repository.py` and `base_notification_service.py`
- No DB migrations required (all fixes are code-only)

---

## Acceptance Scenarios

### US-001 (SQL injection)
**Given** an AdminSettingsRepository with user-controlled `notification_type`
**When** a query is executed with malicious input
**Then** all user-controlled values are parameterized via `:param` bindings, f-string SQL is eliminated

### US-002 (Competition crashes)
**Given** a CompetitionNotificationService with valid student/group/instructor IDs
**When** `notify_team_registration`, `notify_fee_payment`, or `notify_placement` is called
**Then** `_get_student_name`, `_get_group_name`, `_get_instructor_name` resolve correctly
**And** the notification is dispatched without error

### US-003 (get_template_by_code)
**Given** any existing template
**When** `get_template_by_code` is called with its code
**Then** the template is returned (or the method is removed/deprecated if code field does not exist)

### US-005 (Architecture)
**Given** any router in the notifications module
**When** the router needs to query or mutate data
**Then** it calls a public method on the injected service
**And** never accesses `._repo`, `._session`, or other private attributes

### US-007 (Consistent sessions)
**Given** AdminSettingsRepository and NotificationRepository
**When** either creates or updates data
**Then** both use `flush()` (not `commit()`) to let the outer UoW/session manage the transaction
