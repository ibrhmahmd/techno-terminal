# Tasks: Employee Soft Delete with Restore & Re-hire

**Input**: Design documents from `/specs/040-employee-soft-delete/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/hr-employee-lifecycle-api.md ✅, quickstart.md ✅

**Tests**: INCLUDED — spec FR-013 mandates automated regression checks; quickstart.md defines the FR→test coverage map (`tests/test_hr_delete.py`).

**Organization**: Tasks grouped by user story (US1 safe removal → US2 re-hire without conflicts → US3 restore & discovery).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

FastAPI backend at repository root: `app/` (modules under `app/modules/hr/`), `db/`, `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prove a green starting point so regressions introduced by this feature are distinguishable from pre-existing failures

- [X] T001 Record baseline: run `python -m pytest tests/test_hr.py tests/test_hr_full.py tests/test_hr_audit_regressions.py -q` and confirm zero failures (expected: 72 passed, 1 skipped, 2 xpassed)

**Checkpoint**: Baseline recorded — implementation can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database markers + model fields that every user story reads or writes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create migration `db/migrations/079_employee_soft_delete.sql`: `ALTER TABLE employees ADD COLUMN deleted_at TIMESTAMPTZ NULL` and `ADD COLUMN deleted_by INTEGER NULL REFERENCES users(id)`; then `ALTER TABLE employees DROP CONSTRAINT uq_employees_email`, `DROP CONSTRAINT uq_employees_national_id`, `DROP CONSTRAINT uq_employees_phone`; then recreate each as partial unique index with IDENTICAL name (`CREATE UNIQUE INDEX uq_employees_email ON employees (email) WHERE deleted_at IS NULL` etc.). Do NOT touch `uq_employees_user_id`. (Constraint-vs-index form verified live — research D1.)
- [X] T003 [P] Sync schema file: add the two columns to the `employees` CREATE TABLE in `db/schema/02_tables_core.sql` (fresh CI databases must match migrated production)
- [X] T004 [P] Sync schema file: replace the three plain unique index definitions with the partial versions (`WHERE deleted_at IS NULL`) in `db/schema/20_indexes.sql`, keeping names identical
- [X] T005 Add nullable `deleted_at: datetime | None` and `deleted_by: int | None` (foreign_key `users.id`) to the `Employee` model in `app/modules/hr/models/employee_models.py`, mirroring `student_models.py:58-59`

**Checkpoint**: Schema artifacts consistent across migration + fresh-schema paths; model carries markers — user story work can begin

---

## Phase 3: User Story 1 - Safe Removal from All Surfaces (Priority: P1) 🎯 MVP

**Goal**: Admin deletes an employee; the record vanishes from lookup/lists/staff-accounts overview, a linked login can no longer authenticate, historical references stay intact, and double-deletes fail uniformly with 404.

**Independent Test**: Create an employee (optionally linked to a seeded local user), DELETE them, then verify: GET → 404 · default list absent · staff-accounts absent · local `User.is_active == false` when linked · second DELETE → 404 · task/instructor reference rows byte-identical.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [US1] Write failing delete-path suite in `tests/test_hr_delete.py` (`TestDeleteLifecycle`): markers+actor stamped (`deleted_at` non-null, `deleted_by` = acting admin id); hidden from GET/{id}, default list, staff-accounts overview; linked seeded `User.is_active` flipped false; double-delete returns uniform 404 envelope (`NotFoundError`); history preservation assertion (a referencing row, e.g. `tasks.assigned_to`, unchanged); uniform 401s without auth

### Implementation for User Story 1

- [X] T007 [US1] Repository changes in `app/modules/hr/repositories/employee_repository.py`: `get_by_id` returns None for soft-deleted rows; add `soft_delete(employee_id: int, deleted_by: int) -> Employee` (stamps both columns, raises `NotFoundError` if missing or already deleted); extend `list_all(page, page_size, include_deleted=False)` skipping deleted unless flagged
- [X] T008 [US1] Declare changed/added methods in BOTH Protocol interfaces in `app/modules/hr/repositories/interface.py` (`soft_delete`, updated `list_all` signature)
- [X] T009 [US1] Exclude deleted employees from the staff accounts overview: add `Employee.deleted_at.is_(None)` filter to the JOIN in `list_all_with_employees()` in `app/modules/hr/repositories/staff_account_repository.py`
- [X] T010 [US1] Implement `delete_employee(employee_id: int, actor_user_id: int)` in `app/modules/hr/services/employee_crud_service.py`: fetch live target (None → `NotFoundError`), call `set_user_active(user_id, False)` when `user_id` set, stamp markers via repo, single `uow.commit()`; exceptions propagate after rollback (constitution UoW constraint)
- [X] T011 [US1] Add `DELETE /employees/{employee_id}` route in `app/api/routers/hr_router.py`: `Depends(require_admin)` passing `current_user.id` as actor, returns `{"success": true, "data": true, "message": "Employee deleted"}`, NO try/except translation
- [X] T012 [US1] Run `pytest tests/test_hr_delete.py -v` until the US1 class passes; re-run baseline gate to confirm no regression in existing suites

**Checkpoint**: User Story 1 independently functional — removal is safe, complete, and auditable

---

## Phase 4: User Story 2 - Re-hire Without Data Conflicts (Priority: P2)

**Goal**: A deleted employee's national ID / phone / email become reusable; duplicate checks against live records still reject with field-named aggregated conflicts.

**Independent Test**: Delete employee with identity triple X, POST a new employee with exactly X → 201; POST another duplicate of a LIVE employee using X → 409 naming every colliding field.

### Implementation for User Story 2

- [X] T013 [US2] Filter soft-deleted rows out of identity probes in `app/modules/hr/repositories/employee_repository.py`: add `.where(Employee.deleted_at.is_(None))` inside `get_by_national_id`, `get_by_phone`, `get_by_email`
- [X] T014 [US2] Extend `tests/test_hr_audit_regressions.py` with FR-007 lock (`TestFR007ProbesIgnoreDeleted`): create → delete → recreate with identical triple succeeds (201); duplicate probes against the LIVE recreated record still aggregate-conflict; run both suites green

**Checkpoint**: Stories 1 AND 2 work independently — deletion frees identifiers, uniqueness still enforced among the living

---

## Phase 5: User Story 3 - Recoverable Mistakes via Restore & Discovery (Priority: P3)

**Goal**: Admin restores a mistakenly deleted employee (collision-safe), discovers deleted records via `include_deleted=true`, and restore never silently re-enables logins.

**Independent Test**: Delete A → restore A → fully visible again with cleared markers, linked account STILL blocked; restore a live employee → 409 "is not deleted"; after re-hiring B over A's triple X, restoring A → 409 naming every colliding field of X; `GET ?include_deleted=true` lists deleted rows (admin-only).

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [US3] Write failing restore/discovery suite in `tests/test_hr_delete.py` (`TestRestoreLifecycle`, `TestIncludeDeletedFlag`): happy-path restore clears both markers and record reappears everywhere; restore of never-deleted → 409 `ConflictError` "is not deleted"; unknown ID → 404; post-re-hire collision → 409 naming ALL colliding fields together; restored employee's account remains inactive; flag returns deleted rows with populated `deleted_at`/`deleted_by` while default listing stays clean; non-admin use of flag → standard rejection

### Implementation for User Story 3

- [X] T016 [P] [US3] Add optional `deleted_at: datetime | None = None` and `deleted_by: int | None = None` to `EmployeeReadDTO` in `app/modules/hr/schemas/employee_schemas.py`
- [X] T017 [US3] Add `restore(employee_id: int) -> Employee` to `app/modules/hr/repositories/employee_repository.py` (raises `NotFoundError` unknown, `ConflictError` if not deleted; clears both markers) and declare it in `app/modules/hr/repositories/interface.py`
- [X] T018 [US3] Implement `restore_employee(employee_id: int)` in `app/modules/hr/services/employee_crud_service.py`: resolve deleted row (repo raises typed errors), build identity snapshot and run the existing `_validate_unique_fields` aggregation EXCLUDING self against live rows → single field-named `ConflictError` on collision; clear markers; single commit; do NOT touch linked account activation
- [X] T019 [US3] Extend `app/api/routers/hr_router.py`: `POST /employees/{employee_id}/restore` returning full `EmployeeReadDTO` envelope; add `include_deleted: bool = False` Query parameter threaded through `list_employees` service call
- [X] T020 [US3] Thread `include_deleted` through `list_employees(page, page_size, include_deleted)` in `app/modules/hr/services/employee_crud_service.py` and run `pytest tests/test_hr_delete.py -v` until all US3 classes pass

**Checkpoint**: All user stories independently functional — deletion is safe, reversible, discoverable, and re-hire compatible

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature verification and client communication

- [X] T021 Apply `079_employee_soft_delete.sql` to the test database, verify `pg_indexes` shows three partial unique indexes with original names, then run the full HR gate from `quickstart.md` (`test_hr.py` + `test_hr_full.py` + `test_hr_audit_regressions.py` + `test_hr_delete.py`) — zero failures required (SC-005)
- [X] T022 Write client-facing notes `specs/040-employee-soft-delete/frontend-migration-notes.md`: two new endpoints, `include_deleted` query flag, `deleted_at`/`deleted_by` nullable fields on employee payloads, error envelopes for every new failure mode

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — run immediately
- **Foundational (Phase 2)**: blocks ALL user stories (markers/columns must exist)
- **US1 (Phase 3)**: depends on Phase 2 only
- **US2 (Phase 4)**: depends on Phase 2 (probes need `deleted_at` column); logically follows US1 since it deletes records created there
- **US3 (Phase 5)**: depends on Phase 2; uses US1's delete path in its scenarios
- **Polish (Phase 6)**: depends on all stories complete

### User Story Dependencies

- **US1 (P1)**: independent — starts after foundational
- **US2 (P2)**: independent of US3; exercises US1's delete endpoint in its test flow
- **US3 (P3)**: independent of US2; exercises US1's delete endpoint and US2's re-hire behavior in the collision scenario

### Within Each Story

- Tests written first, verified FAILING
- Repositories before services, services before routers
- Protocol declarations alongside repository signatures (same commit acceptable)
- Story checkpoint run before advancing

### Parallel Opportunities

- Phase 2: T003 ∥ T004 (different schema files)
- Phase 5: T016 ∥ T017 (schemas vs repositories files)
- Cross-story: US2 and US3 touch disjoint production files except `employee_crud_service.py` (T013 vs T018 sequential recommended) and `hr_router.py` (T011 vs T019 sequential)

---

## Parallel Example

```bash
# Phase 2 (after T002):
Task: "Sync db/schema/02_tables_core.sql columns"      # T003
Task: "Sync db/schema/20_indexes.sql partial indexes"  # T004

# Phase 5 (after T015):
Task: "Add marker fields to EmployeeReadDTO"           # T016
Task: "Repository restore() + Protocol declaration"    # T017
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phases 1–2 (baseline + schema/model foundation)
2. Complete Phase 3 → **STOP and VALIDATE**: safe removal works end-to-end
3. Deploy/demo if ready — already closes the security gap (login auto-block)

### Incremental Delivery

1. Foundation → 2. US1 (MVP) → validate → 3. US2 re-hire support → validate → 4. US3 restore & discovery → validate → 5. Full-gate polish

Each increment leaves the HR suite green per its checkpoint.

---

## Notes

- [P] tasks = different files, no dependencies
- Same-name partial indexes are LOAD-BEARING: never rename during any refactor — the IntegrityError mapper matches on them (research D1)
- Restore deliberately does NOT unblock logins (spec FR-011) — do not "helpfully" add it
- Commit after each task or logical group; stop at any checkpoint to validate the story independently
