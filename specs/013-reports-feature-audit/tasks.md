---

description: "Task list for daily report bug fixes — Reports Feature Audit"
---

# Tasks: Reports Feature — Daily Report Fixes

**Input**: Design documents from `specs/013-reports-feature-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Scope**: Daily report only. Weekly/monthly/scheduler issues are documented but **deferred** per plan.md.

**User Stories (scoped to daily)**:
- **US1**: Daily report has accurate attendance metrics (P1)
- **US5**: Template variables match what the email body renders (P2) — daily report template only
- **US7**: Manual HTTP trigger exists for on-demand daily reports (P2)

---

## Phase 1: Foundational — New Files

**Purpose**: Create the typed DTO and repository layer before modifying the service. Migration SQL is independent.

**⚠️ CRITICAL**: T001–T003 must be complete before US1 service modifications begin.

- [ ] T001 [P] Create `DailyReportAggregateDTO` + `PaymentDetailItem` in `app/modules/notifications/schemas/report_dto.py`
- [ ] T002 [P] Create `ReportsRepository.get_daily_aggregates()` in `app/modules/notifications/repositories/reports_repository.py` — encapsulate all 7 aggregate queries (revenue via COALESCE, sessions, attendance with present/absent/cancelled only, enrollments via COALESCE, payments, instructors, unpaid count)
- [ ] T003 [SKIP] Migration already exists as `052_update_daily_report_template_body.sql` — no new migration needed

**Checkpoint**: Foundation ready — US1 service modifications can now begin.

---

## Phase 2: User Story 1 — Accurate Daily Report Metrics (P1) 🎯 MVP

**Goal**: Daily report attendance counts use actual domain values (`present`, `absent`, `cancelled` — no `late`/`excused`), revenue/enrollment queries apply COALESCE fallbacks for NULL timestamps, all queries delegate to `ReportsRepository`, and return type is `DailyReportAggregateDTO`.

**Independent Test**: Run `pytest tests/ -v -k daily` after implementation — verify report processes without errors and produces non-zero revenue/enrollment values.

### Implementation for User Story 1

- [ ] T004 [US1] Fix attendance query in `_fetch_daily_aggregates()`: remove `late`/`excused` filters, count only `present`, `absent`, `cancelled` in `app/modules/notifications/services/report_notifications.py`
- [ ] T005 [US1] Fix COALESCE fallbacks in `app/modules/notifications/services/report_notifications.py`: apply `COALESCE(paid_at, created_at)` for payment queries and `COALESCE(enrolled_at, created_at)` for enrollment count queries
- [ ] T006 [US1] Delegate all aggregate queries from `_fetch_daily_aggregates()` in `app/modules/notifications/services/report_notifications.py` to call `ReportsRepository.get_daily_aggregates()` instead of inline raw SQL
- [ ] T007 [US1] Replace bare `dict` return type in send_daily_report() call chain with `DailyReportAggregateDTO` in `app/modules/notifications/services/report_notifications.py`
- [ ] T008 [US1] Delete commented-out PARENT_CODE dead code block at `report_notifications.py:429-441`

**Checkpoint**: US1 complete — daily report now produces correct attendance counts, non-zero revenue/enrollment values, and uses typed DTOs.

---

## Phase 3: User Story 7 — Manual HTTP Trigger (P2)

**Goal**: Admin can trigger daily report on-demand via REST API.

**Independent Test**: Send `POST /api/v1/notifications/reports/daily` with admin JWT — expect `202` or `200` with success envelope.

### Implementation for User Story 7

- [ ] T009 [P] [US7] Add `POST /api/v1/notifications/reports/daily` endpoint in `app/api/routers/notifications/notifications_router.py` using `require_admin` guard + `BackgroundTasks.add_task(svc.report.send_daily_report)`

**Checkpoint**: US7 complete — daily report can be triggered on-demand.

---

## Phase 4: Cross-Cutting & Polish

**Purpose**: Fixes not tied to a single user story — SQL injection prevention.

- [ ] T010 Fix f-string SQL interpolation in `_resolve_notification_recipients()` in `app/modules/notifications/services/base_notification_service.py` — replace `f"'...' = ANY(...)"` with parameterized `:notification_type = ANY(...)`

**Checkpoint**: All daily report fixes complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — T001, T002 can run in parallel
- **US1 (Phase 2)**: Depends on T001 (DTO exists) and T002 (Repository exists)
- **US7 (Phase 3)**: Depends on US1 (Phase 2) completion — service must be fixed before triggering
- **Polish (Phase 4)**: No dependencies on other phases — T010 fully independent

### User Story Dependencies

- **US1 (P1)**: Depends on T001, T002 — No dependencies on other stories
- **US7 (P2)**: Depends on US1 completion
- **Polish**: No dependencies

### Within Each Phase

- New files before service modifications
- Repository before delegation
- Service fixes before endpoint creation

### Parallel Opportunities

- T001, T002 in Phase 1 can run in parallel (different files, no dependencies)
- T004–T008 within US1 are sequential (same file)
- T010 is fully independent — can run anytime
- Phase 2 (US1) and Phase 4 (Polish) can run in parallel (different files, different concerns)
- Phase 3 (US7) must wait for Phase 2 (US1) completion

---

## Parallel Example: Phase 1

```bash
# Launch both foundation tasks together:
Task: "Create DTO in app/modules/notifications/schemas/report_dto.py"
Task: "Create repository in app/modules/notifications/repositories/reports_repository.py"
```

## Parallel Example: Phase 2 + 4

```bash
# US1 service fixes and Polish can run in parallel:
Task: "Fix attendance, COALESCE, delegate to repo, use DTO, delete dead code"
Task: "Fix SQL injection in base_notification_service.py"
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2 Only)

1. Complete Phase 1: Foundational (DTO, Repository)
2. Complete Phase 2: US1 — accurate daily report (fix bugs, use typed DTO)
3. **STOP and VALIDATE**: Run `pytest tests/ -v` — daily report processes with correct values
4. Deploy/demo if ready — core bugs fixed

### Incremental Delivery

1. Phase 1 (Foundation) → DTO, Repository ready
2. Phase 2 (US1) → Core bug fixes applied → **MVP complete**
3. Phase 3 (US7) → HTTP trigger available
4. Phase 4 (Polish) → SQL injection fixed

### Parallel Strategy

With multiple developers:
- Developer A: Phase 1 tasks (all parallel)
- Developer B: Phase 4 (independent T010)
- After Phase 1: Developer A → Phase 2 (US1), Developer B → Phase 3 (US7)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each phase
- Stop at any checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
