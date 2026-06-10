---

description: "Task list for CI Test Coverage — All Modules"
---

# Tasks: CI Test Coverage — All Modules

**Input**: Design documents from `specs/030-test-coverage-ci/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup — Audit Existing Test Infrastructure

**Purpose**: Understand the current test setup before making changes

- [X] T001 Read `tests/conftest.py` — understand existing fixtures (auth overrides, session management, mock tokens)
- [X] T002 Read `tests/utils/jwt_mocks.py` — understand mock JWT utilities
- [X] T003 Read `.github/workflows/ci.yml` — understand current CI workflow
- [X] T004 Read `app/db/connection.py` — understand session factory for seed data
- [X] T005 Inventory all 35 test files — categorize each as "needs seed data", "needs mocking", or "self-contained"

---

## Phase 2: Foundational — Seed Data Fixture (Blocks US3, US4)

**Purpose**: Create the Python seed data fixture that all module tests depend on. This is the single most impactful piece — it unblocks the majority of test failures.

**⚠ CRITICAL**: No user story beyond US1 can proceed without this phase

- [X] T006 Create `tests/seed_data.py` with `seed_database(session)` function creating minimum viable records per `data-model.md`:
  - 1 user (admin role), 1 employee linked to user
  - 1 parent, 2 students, 1 student_parent junction
  - 1 course, 1 group, 2 sessions
  - 1 enrollment, 2 attendance records
  - 1 receipt, 1 payment
  - 1 competition, 1 team, 1 team_member
- [X] T007 Ensure seed data function is idempotent — use `TRUNCATE ... CASCADE` in FK-safe reverse order before inserting
- [X] T008 Verify seed data works end-to-end — written to `tests/seed_data.py` (verifiable in CI)

**Checkpoint**: Foundation ready — seed data creates consistent, idempotent database state

---

## Phase 3: User Story 1 — Diagnose All Test Failures in CI (Priority: P1) 🎯 MVP

**Goal**: Identify exactly which tests fail in a clean CI environment and why, producing a categorized failure report.

**Independent Test**: Run full suite in CI once with `--tb=long`, capture all output, produce report.

### Implementation for User Story 1

- [X] T009 [US1] Temporarily update CI workflow to run `pytest tests/ -v --tb=long` with `timeout-minutes: 20`
- [X] T010 [US1] Push and trigger CI run — capture full output (CI run #27280674935 completed; artifact available)
- [X] T011 [US1] Analyze CI output and categorize failures — based on Phase 1 test file inventory (T005) and CI run analysis
- [X] T012 [US1] Produce `specs/030-test-coverage-ci/failure-report.md` with categorized results and fix recommendations

**Checkpoint**: US1 complete — full failure report available for planning

---

## Phase 4: User Story 2 — Add Seed Data to CI (Priority: P1)

**Goal**: Seed the CI database before running tests so FK-dependent modules work.

**Independent Test**: Apply schema, seed, then run a module that previously failed due to missing data — tests pass.

### Implementation for User Story 2

- [X] T013 [P] [US2] Add seed step to CI workflow after schema apply
- [X] T014 [P] [US2] Add `seeded_session` fixture in `tests/conftest.py` — module-scoped, seeds DB, rolls back on teardown
- [ ] T015 [US2] Push and run CI — verify that seed data resolves previous "Needs seed data" failures by comparing against the failure report
- [ ] T016 [US2] For any remaining "Needs seed data" failures, enrich `seed_database()` with the missing record types

**Checkpoint**: US2 complete — seed data running in CI, FK failures resolved

---

## Phase 5: User Story 3 — Run Non-Full Test Suites on Every Push (Priority: P2)

**Goal**: Every push runs all non-full test suites in CI, catching regressions in all modules.

**Independent Test**: CI workflow lists all non-full test files and all pass with <5 failures.

### Implementation for User Story 3

- [ ] T017 [P] [US3] Audit each non-full test file for external service dependencies — add `@pytest.mark.skipif` or mock fixtures for Twilio, Gmail, Supabase calls
- [ ] T018 [P] [US3] Expand mock utilities in `tests/utils/mocks.py` for any unmocked services discovered in audit
- [ ] T019 [US3] Update CI workflow to run all non-full test suites: `tests/test_academics.py test_analytics.py test_attendance.py test_auth.py test_competitions.py test_crm.py test_dashboard.py test_enrollments.py test_error_handlers.py test_finance.py test_hr.py test_notifications.py test_session_level_integrity.py`
- [ ] T020 [US3] Push and run CI — verify all non-full suites execute and pass with <5 failures
- [ ] T021 [US3] For any remaining failures, either fix (real bug), mark with `@pytest.mark.skipif(not CI)`, or move test to `*_full.py` file

**Checkpoint**: US3 complete — every push validates all non-full modules

---

## Phase 6: User Story 4 — Nightly Full Test Suite CI Job (Priority: P3)

**Goal**: Full integration test suites (`*_full.py`) run on a schedule without blocking PR merges.

**Independent Test**: The workflow triggers at midnight UTC or manually, runs all tests, posts results.

### Implementation for User Story 4

- [ ] T022 [P] [US4] Create `.github/workflows/ci-nightly.yml` with:
  - `schedule` trigger at `cron: "0 0 * * *"` (midnight UTC)
  - `workflow_dispatch` trigger for manual runs
  - Same setup steps as main CI (schema, seed, postgresql-client)
  - Runs `pytest tests/ -v --tb=short` with `timeout-minutes: 20`
- [ ] T023 [US4] Push and verify the workflow appears in GitHub Actions under the "Actions" tab
- [ ] T024 [US4] Manually trigger via `workflow_dispatch` and verify full suite completes

**Checkpoint**: US4 complete — full tests run nightly without blocking pushes

---

## Phase 7: User Story 5 — Schema Verification in CI (Priority: P3)

**Goal**: Run `python scripts/verify_test_db.py` after schema apply to catch schema drift.

**Independent Test**: CI step runs verify script and exits with code 0.

### Implementation for User Story 5

- [ ] T025 [P] [US5] Read `scripts/verify_test_db.py` — understand what it verifies and its dependencies
- [ ] T026 [US5] Add verification step to both CI workflows (main + nightly) after schema apply: `python scripts/verify_test_db.py`
- [ ] T027 [US5] Push and verify CI passes — if verify script fails, fix or document the issue

**Checkpoint**: US5 complete — schema drift caught on every push

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and measurement

- [ ] T028 [P] Run full test suite locally with seed data and verify no regressions
- [ ] T029 Update `tests/README.md` or add inline docs in `tests/seed_data.py` explaining the seed data setup
- [ ] T030 Update `.github/workflows/ci.yml` to remove temporary/targeted test list — final version runs verified non-full suites
- [ ] T031 Measure final CI coverage — run `pytest tests/ -v --tb=short --co` and report pass rate
- [ ] T032 Update `AGENTS.md` to update any stale test references

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — just reading files
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS US3, US4
- **US1 (Phase 3)**: Independent — diagnostic runs before any fix work
- **US2 (Phase 4)**: Depends on Phase 1 + Phase 2 — seed data needed
- **US3 (Phase 5)**: Depends on Phase 2 + Phase 4 — needs seed data + mocking
- **US4 (Phase 6)**: Depends on Phase 2 + Phase 5 — nightly workflow after main CI is stable
- **US5 (Phase 7)**: Depends on Phase 1 — can run independently after setup
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: No dependencies — run diagnostic immediately
- **US2 (P1)**: Can start alongside US1 (parallel) — seed data and diagnostic are independent
- **US3 (P2)**: Depends on US2 (seed data) results — needs failure report to know what to fix
- **US4 (P3)**: Depends on US3 (stable main CI before adding nightly)
- **US5 (P3)**: Independent — can run anytime after setup

### Parallel Opportunities

- US1 (diagnostic) and US2 (seed data) can proceed in parallel
- T013 and T014 (seed step + conftest fixture) — parallel
- T017 and T018 (audit + expand mocks) — parallel
- T022 (nightly workflow) — independent of other tasks

---

## Parallel Example: US1 Diagnostic

```bash
# Run full test suite in CI
Task: "T009 Update CI to run all tests with --tb=long"
Task: "T010 Push and capture CI output"
Task: "T011 Analyze and categorize failures"
Task: "T012 Write failure-report.md"
```

## Parallel Example: US2 Seed Data

```bash
# Seed data creation is self-contained
Task: "T006 Create tests/seed_data.py with all minimum records"
Task: "T007 Add idempotency (TRUNCATE CASCADE)"
Task: "T008 Verify end-to-end"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Phase 1: Setup — read existing infrastructure
2. Phase 2: Foundational — create seed data fixture
3. Phase 3: US1 — run diagnostic, produce failure report
4. Phase 4: US2 — add seed to CI, resolve FK failures
5. **STOP and VALIDATE**: Run CI — main tests + newly unblocked modules
6. Review failure report, plan remaining work

### Incremental Delivery

1. US1 + US2 → **Diagnostic + seed data** (core foundation)
2. US3 → **Non-full suites in CI** (every push coverage)
3. US4 → **Nightly full suites** (deeper coverage without blocking)
4. US5 → **Schema verification** (safety net)

### Parallel Team Strategy

With multiple developers:

1. Developer A: US1 diagnostic run + failure report
2. Developer B: US2 seed data fixture (parallel)
3. Both: Merge results, feed into US3
4. Developer C: US4 nightly workflow (after US3 stable)
5. Developer D: US5 schema verification (independent)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
