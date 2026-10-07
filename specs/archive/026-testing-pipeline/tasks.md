# Tasks: Testing Pipeline & CI/CD

**Input**: Design documents from `specs/026-testing-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ci-workflow.md

**Tests**: No test tasks — this is infrastructure/testing setup, not feature code.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend repo**: `app/`, `tests/`, `db/`, `.github/` at repository root (`techno_data_ Copy`)
- **Frontend repo**: `src/`, `package.json` at `techno_terminal_UI/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing test infrastructure and set up foundational tooling

- [ ] T001 Verify `.env.test` exists and `config.py` auto-detection works (line 106 of `app/core/config.py` — loads `.env.test` when `PYTEST_CURRENT_TEST` is set)
- [ ] T002 [P] Create `.github/` directory structure at `.github/workflows/`
- [ ] T003 [P] Verify `db/schema.sql` can apply cleanly against a fresh PostgreSQL database (run `psql -f db/schema.sql` against local test DB)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Mock external services so tests never call real Twilio/Gmail/Supabase, and ensure schema is reproducible

- [ ] T004 Create notification mock dispatchers in `tests/utils/notification_mocks.py` that replace `email_dispatcher.py` and Twilio dispatcher with no-op implementations for test context
- [ ] T005 [P] Verify all existing `pytest tests/` tests pass against local test DB without hitting real external services
- [ ] T006 Document the complete local test DB setup process in `specs/026-testing-pipeline/quickstart.md` (schema apply, migration order, `.env.test` configuration)

---

## Phase 3: User Story 1 — Local Test Database (Priority: P1) 🎯 MVP

**Goal**: A developer can run the full test suite locally against a safe test database with zero risk of touching production.

**Independent Test**: Run `pytest tests/ -v` and confirm all tests pass using the local PostgreSQL database indicated in `.env.test`, with no queries going to production.

- [ ] T007 [US1] Create schema reproducibility verification script at `scripts/verify_test_db.py` that applies `db/schema.sql` to a target database and reports any errors
- [ ] T008 [US1] Add a section to `AGENTS.md` under "Commands" documenting how to run tests locally with `.env.test`
- [ ] T009 [US1] Validate end-to-end: `pytest tests/ -v` passes cleanly against local test DB (confirm no tests skipped due to missing external services)

**Checkpoint**: Local test DB is fully operational — developer can safely run tests.

---

## Phase 4: User Story 2 — GitHub Actions CI Pipeline (Priority: P2)

**Goal**: Every push/PR automatically triggers a CI pipeline that runs the full test suite in an isolated cloud environment.

**Independent Test**: Push a commit to GitHub and observe the CI workflow trigger, provision PostgreSQL, apply schema, run `pytest`, and report pass/fail.

- [ ] T010 [US2] Create `.github/workflows/ci.yml` with backend test job: PostgreSQL 15 service container, schema init via `db/schema.sql`, `pytest tests/ -v --cov=app --cov-report=term-missing`
- [ ] T011 [US2] Configure CI environment variables in `.github/workflows/ci.yml` for all external services (Supabase, Twilio, Gmail) using dummy/mock-safe values per `contracts/ci-workflow.md`
- [ ] T012 [US2] Validate CI YAML syntax with `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`

**Checkpoint**: Backend CI pipeline runs and reports results on every push.

---

## Phase 5: User Story 3 — Frontend Build Validation (Priority: P3)

**Goal**: CI also validates the frontend builds successfully (TypeScript compilation + Vite build).

**Independent Test**: Introduce a TypeScript error in a frontend file, push to GitHub, and observe the CI pipeline report failure on the frontend build step.

- [ ] T013 [US3] Add frontend checkout + build job to `.github/workflows/ci.yml` that checks out `techno_terminal_UI`, runs `npm ci`, and runs `npm run build`
- [ ] T014 [US3] Validate frontend build passes locally: `cd ../techno_terminal_UI && npm run build` completes with exit code 0

**Checkpoint**: Both backend tests and frontend build validate automatically on every push.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation updates and verification

- [ ] T015 Update `AGENTS.md` — remove the "No CI / Linter / Formatter" note at line 100 and replace with a "CI Pipeline" section referencing `.github/workflows/ci.yml`
- [ ] T016 Final validation: run `pytest tests/ -v`, verify CI YAML is valid, confirm quickstart instructions are accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify existing infrastructure
- **Foundational (Phase 2)**: Depends on Setup — creates mocks and validates schema
- **US1 (Phase 3)**: Depends on Foundational — need working test DB and mocks
- **US2 (Phase 4)**: Depends on Foundational — CI needs schema reproducibility and mocks; can run in parallel with US1
- **US3 (Phase 5)**: Depends on US2 (extends the same `.github/workflows/ci.yml`)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Local test DB — foundation for all testing
- **US2 (P2)**: CI pipeline — needs US1 concepts but can be built in parallel (CI uses its own PostgreSQL service, not local DB)
- **US3 (P3)**: Frontend build in CI — extends US2's workflow file

### Parallel Opportunities

- T002, T003 can run in parallel (setup tasks)
- T004, T005, T006 can run in parallel (foundational phase)
- US1 tasks and US2 tasks can run in parallel once foundational phase completes
- T010 and T011 (US2) can run in parallel
- T013 and T014 (US3) can run in parallel

---

## Parallel Example: US1 + US2

```bash
# US1 tasks (independent from US2):
Task: "Create schema reproducibility verification script at scripts/verify_test_db.py"
Task: "Add test documentation to AGENTS.md"

# US2 tasks (can run at same time):
Task: "Create .github/workflows/ci.yml"
Task: "Configure CI environment variables"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1
4. **STOP and VALIDATE**: `pytest tests/ -v` passes locally

### Incremental Delivery

1. Setup + Foundational → Mocks and schema ready
2. US1 complete → Local test DB validated (MVP!)
3. US2 complete → GitHub Actions CI running
4. US3 complete → Full CI with frontend build validation
