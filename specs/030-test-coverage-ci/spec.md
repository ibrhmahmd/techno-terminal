# Feature Specification: CI Test Coverage — All Modules

**Feature Branch**: `030-test-coverage-ci`
**Created**: 2026-06-10
**Status**: Draft
**Input**: User request: "finalize testing to cover all the app gaps"

## Clarifications

### Session 2026-06-10

- Q: What format should the seed data be in? → A: Python fixture (`tests/seed_data.py` or shared conftest) using SQLModel models, preferred over raw SQL.
- Q: Should the 80% coverage target include `*_full.py` tests? → A: Yes — include all 864 tests, `*_full.py` included.
- Q: How should tests be isolated from each other's DB side effects? → A: Per-test-file transaction rollback — seed data applied once per file, session rolls back on teardown.
- Q: How should external service calls (Twilio, Supabase, Gmail) be handled in CI? → A: Mock at the test level — add pytest fixtures that intercept external calls. Tests that can't be mocked get `@pytest.mark.skipif(not CI)`.
- Q: What's the diagnostic approach for US1 — run with `--maxfail=5` or capture all failures? → A: Capture ALL failures for a full report, not just first 5. Run the complete suite once with `--tb=long`, collect the full output, and produce a categorized failure report for planning.

## Context

Current CI runs only `tests/test_finance.py` (32 tests) and `tests/test_crm.py` (26 tests) = **58/864 tests** (6.7% coverage). The other 806 tests across 30 test files are never validated in CI because they require database state that doesn't exist on a fresh schema-only database.

| Module | Tests | CI? | Gap |
|--------|-------|-----|-----|
| Finance | 32 | ✅ | — |
| CRM | 26 | ✅ | — |
| Academics | 168 | ❌ | Needs seed data / mocking |
| Analytics | 149 | ❌ | Needs seed data / mocking |
| Auth | 89 | ❌ | Needs seed data / mocking |
| Competitions | 58 | ❌ | Needs seed data / mocking |
| Enrollments | 41 | ❌ | Needs seed data / mocking |
| Attendance | 27 | ❌ | Needs seed data / mocking |
| HR | 60 | ❌ | Needs seed data / mocking |
| Notifications | 46 | ❌ | Needs seed data / mocking |
| Error Handlers | 12 | ❌ | May work with mocking |
| Dashboard | 10 | ❌ | Needs seed data / mocking |
| Session Integrity | 18 | ❌ | Needs seed data / mocking |
| Connection Exhaustion | 7 | ❌ | Needs DB setup |
| **Total** | **864** | **58 (6.7%)** | **806 (93.3%)** |

## User Scenarios & Testing

### User Story 1 — Diagnose All Test Failures in CI (Priority: P1)

As a CI maintainer, I want to identify exactly which tests fail in a clean CI environment and why, so I can determine the minimal fixes needed.

**Why this priority**: We can't fix what we don't measure. A full CI run with detailed output is needed before any remediation work.

**Independent Test**: Run `pytest tests/ -v --tb=long` in CI with a fresh database, capture ALL failure output for a categorized report.

**Acceptance Scenarios**:

1. **Given** a fresh PostgreSQL database with only `db/schema.sql` applied, **When** the full test suite is run in CI, **Then** the output is captured showing each failure with traceback.
2. **Given** the failure output, **When** analyzed, **Then** each failure is categorized as:
   - "Needs seed data" — test requires specific DB records
   - "Needs mocking" — test relies on external service (Supabase, Twilio)
   - "Needs environment variable" — test requires specific env config
   - "Real bug" — legitimate code defect

---

### User Story 2 — Add CI-Compatible Seed Data Fixture (Priority: P1)

As a test author, I want a seed data script that populates a fresh database with enough reference data so that all integration tests can run without manual setup.

**Why this priority**: 70%+ of test failures are due to missing data (students, courses, groups, users, etc.). A seed fixture unblocks almost all modules at once.

**Independent Test**: Apply schema, run seed script, then run all `test_*` (not `*_full`) tests — they should all pass.

**Acceptance Scenarios**:

1. **Given** a fresh database with schema applied, **When** the seed data script is run, **Then** all FK references are satisfied: at least 1 user, 2 students, 1 course, 1 group, 2 sessions, 1 enrollment, 1 receipt exist.
2. **Given** seeded database, **When** `pytest tests/test_academics.py tests/test_enrollments.py tests/test_attendance.py` is run, **Then** all tests pass.

---

### User Story 3 — Run "Non-Full" Test Suites in CI (Priority: P2)

As a CI maintainer, I want every `test_<module>.py` (not `test_<module>_full.py`) to run in CI so that core module tests are validated on every push.

**Why this priority**: The "full" test suites (`*_full.py`) are integration-heavy. The regular test files are mostly unit/service tests that should pass with minimal seed data.

**Independent Test**: The CI workflow runs `pytest tests/test_academics.py tests/test_analytics.py tests/test_attendance.py tests/test_auth.py tests/test_competitions.py tests/test_enrollments.py tests/test_error_handlers.py tests/test_hr.py tests/test_notifications.py` and all pass.

**Acceptance Scenarios**:

1. **Given** CI with schema + seed data, **When** all non-full test suites are run, **Then** tests pass with <5 failures.
2. **Given** any failure, **When** investigated, **Then** it's either a real bug (filed separately) or a test that needs the `_full` label or xfail marker.

---

### User Story 4 — Add "Full" Test Suite CI Job (Nightly/Manual) (Priority: P3)

As a developer, I want the `*_full.py` integration test suites to run on a schedule or on-demand so that deep integration issues are caught without blocking every push.

**Why this priority**: Full test suites are slow and data-dependent. They shouldn't block CI, but should run periodically.

**Independent Test**: A separate CI workflow (or cron trigger) runs `pytest tests/ -k "_full"` and reports results.

**Acceptance Scenarios**:

1. **Given** a scheduled CI trigger, **When** the full test suites run, **Then** results are posted without blocking PR merges.
2. **Given** a manual workflow_dispatch trigger, **When** triggered, **Then** full test suites execute.

---

### User Story 5 — Add Verification Test for CI Schema Freshness (Priority: P3)

As a developer, I want a CI step that verifies the schema.sql file is reproducible and matches the migration chain, so schema drift is caught early.

**Why this priority**: The AGENTS.md mentions `scripts/verify_test_db.py` exists for this purpose. Running it in CI adds a safety net.

**Independent Test**: CI step runs `python scripts/verify_test_db.py` after schema apply and before tests.

**Acceptance Scenarios**:

1. **Given** schema applied to fresh database, **When** `python scripts/verify_test_db.py` runs, **Then** it exits with code 0.

---

### Edge Cases

- What if seed data conflicts with test assumptions (e.g., test expects empty DB)?
- What if a test modifies seed data (leaves side effects for next test)?
- What about tests that need real Supabase JWTs vs mock tokens?
- How to handle tests that call external APIs (Twilio, Gmail)?

## Requirements

### Functional Requirements

- **FR-001**: CI MUST run all non-full test suites on every push (P1).
- **FR-002**: CI MUST have a seed data script that creates minimum viable reference data for all modules (P1).
- **FR-003**: CI MUST include a diagnostic run step that captures and categorizes test failures (P1).
- **FR-004**: The seed data script MUST be idempotent (safe to run multiple times) (P1).
- **FR-005**: Tests that require real external services MUST be mock-safe and not fail in CI (P2).
- **FR-006**: The `*_full.py` test suites MUST NOT block the main CI pipeline (P2).
- **FR-007**: Full test suites SHOULD run on a schedule (nightly) or manual trigger (P3).
- **FR-008**: Schema reproducibility verification SHOULD run in CI (P3).

### Key Entities

- **CI Database**: Fresh PostgreSQL 15 with `db/schema.sql` only (no seed data currently)
- **Seed Data Script**: `db/ci_seed.sql` or equivalent — creates reference records (users, students, courses, groups, sessions, receipts)
- **Test Categories**:
  - `test_<module>.py` — Unit/service tests, mock-friendly, no DB state dependency
  - `test_<module>_full.py` — Integration tests, need seeded DB, may test external integrations

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least 80% of all 864 tests (including `*_full.py`) pass in CI (from current 6.7%)
- **SC-002**: Every push runs tests for all non-full modules
- **SC-003**: Seed data script creates a consistent, idempotent database state
- **SC-004**: Zero CI failures caused by missing seed data (only real bugs or env issues)
- **SC-005**: Full integration tests run nightly without developer intervention

## Assumptions

- Pre-existing tests were written with specific database state expectations (seeded dev DB)
- "Full" test suites (`*_full.py`) are more integration-heavy and may need richer data
- Tests that need real Supabase JWTs can use the mock token utilities (`tests/utils/jwt_mocks.py`)
- External service calls (Twilio, Gmail) are already mocked in the test fixtures or can be skipped
- The `scripts/verify_test_db.py` script works and is maintained
