# Implementation Plan: CI Test Coverage — All Modules

**Branch**: `030-test-coverage-ci` | **Date**: 2026-06-10 | **Spec**: `specs/030-test-coverage-ci/spec.md`
**Input**: Feature specification from `specs/030-test-coverage-ci/spec.md`

## Summary

Expand CI test coverage from 58/864 tests (6.7%) to 80%+ by: running a diagnostic to capture all failures, creating a Python seed data fixture for CI, mocking external services, adding per-test-file transaction isolation, and running non-full test suites on every push plus full suites nightly.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: pytest, SQLModel, FastAPI, PostgreSQL
**Storage**: PostgreSQL 15 (CI service container)
**Testing**: pytest, mock JWT utilities (`tests/utils/jwt_mocks.py`), dummy env vars for external services
**Target Platform**: GitHub Actions (ubuntu-latest)
**Project Type**: Web service (FastAPI backend)
**Performance Goals**: CI test suite completes within 10 minutes
**Constraints**: Fresh DB per CI run (schema only, no seed data currently); external services (Twilio, Gmail, Supabase) must be mocked; tests must not leave side effects
**Scale/Scope**: 35 test files, 864 tests across 12 business modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Post-Design Re-check (Phase 1 Complete)

- ✅ **Gate 1 — Layer Separation**: Seed data fixture in `tests/`, no layer violations.
- ✅ **Gate 2 — Typed Contracts**: No new interfaces. Seed data uses existing SQLModel models.
- ✅ **Gate 3 — Exception Mapping**: No exception changes.
- ✅ **Gate 4 — Dead Code**: No dead code involved.
- ✅ **Gate 5 — Test Isolation**: Per-test-file transaction rollback prevents contamination.

**Overall: ✅ ALL GATES PASS**

### Gate 1 — Layer Separation (§I)
- ✅ **PASS**: Seed data fixture lives in `tests/` (test infrastructure), mock utilities remain in `tests/utils/`. No layer violations.

### Gate 2 — Typed Contracts (§III)
- ✅ **PASS**: No new service/repository interfaces involved. Seed data uses existing SQLModel models.

### Gate 3 — Exception Mapping (§IV)
- ✅ **PASS**: No changes to exception handling.

### Gate 4 — Dead Code (§Dead Code)
- ✅ **PASS**: No dead code involved. Adding new test infrastructure, not modifying existing.

### Gate 5 — Test Isolation
- ✅ **PASS**: Per-test-file transaction rollback (chosen in clarify) prevents cross-test contamination. No shared mutable state.

**Overall: ✅ GATE PASSED** — No violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-test-coverage-ci/
├── plan.md              # This file
├── spec.md              # Feature specification (with clarifications)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output — seed data entity relationships
├── quickstart.md        # Phase 1 output — CI verification steps
├── contracts/           # Phase 1 output — CI workflow contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Files created or modified by this feature
.github/workflows/
└── ci.yml                       # Expanded to run more test suites + nightly schedule

tests/
├── seed_data.py                 # NEW: Python seed data fixture using SQLModel models
├── conftest.py                  # MODIFIED: add seed data hooks, per-file transaction
├── utils/
│   └── mocks.py                 # MODIFIED/EXPANDED: external service mocks
├── test_finance.py              # Already works
├── test_crm.py                  # Already works
├── test_academics.py            # Target for CI enablement
├── test_analytics.py            # Target for CI enablement
├── ...                          # Other non-full test suites
└── ..._full.py                  # Nightly-only (separate workflow)

db/
└── ci_seed.sql                  # (optional, fallback if Python fixture insufficient)
```

**Structure Decision**: Single backend monorepo. Test infrastructure lives under `tests/`. CI config under `.github/workflows/`.

## Complexity Tracking

*No constitution violations to justify. Table omitted.*
