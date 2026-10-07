# Research: CI Test Coverage — All Modules

**Branch**: `030-test-coverage-ci`
**Date**: 2026-06-10
**Status**: Complete

## Diagnostic Strategy

### Current State
- CI runs only `tests/test_finance.py` + `tests/test_crm.py` = 58/864 tests (6.7%)
- Database is fresh schema-only — no seed data
- External services use dummy env vars (no real credentials in CI)

### Approach
1. **Phase 1 — Diagnostic**: Run ALL tests in CI with `--tb=long`, capture full output, categorize failures
2. **Phase 2 — Seed data**: Create Python fixture (`tests/seed_data.py`) using SQLModel models
3. **Phase 3 — Mock expansion**: Ensure all external services are mocked in CI
4. **Phase 4 — CI expansion**: Run non-full suites on every push, full suites nightly

## Seed Data Design

### Decision
- **Decision**: Python fixture in `tests/seed_data.py` using SQLModel models
- **Rationale**: Type-safe, uses same ORM as app, reusable in conftest fixtures, maintainable
- **Alternatives considered**: Raw SQL script (`db/ci_seed.sql`) — faster but brittle and duplicates model logic

### Minimum Viable Records
Based on FK dependency chain:
```
users (1 admin) → courses (1 math) → groups (1 group A)
                → students (2: Ahmed, Sara) → enrollments (1)
                → sessions (2) → attendance (2 records)
                → receipts (1) → payments (1)
```

### Idempotency
- Use `DELETE FROM ... CASCADE` or `TRUNCATE ... CASCADE` before INSERT
- Alternatively, wrap each seed in a transaction that rolls back after test file completes

## Test Isolation

### Decision
- **Decision**: Per-test-file transaction rollback
- **Rationale**: Seed data applied once per file via pytest session fixture. All tests in the file share a transaction that rolls back on teardown. This is the existing pattern used by some modules.
- **Alternatives considered**: Per-test transaction (slow), no isolation (side-effect bugs)

## External Service Mocking

### Decision
- **Decision**: Mock at test level using pytest fixtures + `unittest.mock`
- **Rationale**: Already partially done (`tests/utils/jwt_mocks.py`). Need to audit each module for unmocked calls.
- **Services needing mocks**: Supabase (JWT validation), Twilio (WhatsApp), Gmail (email), SMS

## CI Workflow Design

### Decision
- **Decision**: Two workflows — main CI (every push) + nightly (full suites)
- **Main CI**: schema → seed → non-full tests (target: <5 failures)
- **Nightly CI**: schema → seed → full suites (cron: midnight UTC)
- **Rationale**: Full suites are slower and may need richer data. Non-full suites catch regressions quickly.

## References

- `tests/conftest.py` — existing pytest fixtures and hooks
- `tests/utils/jwt_mocks.py` — existing mock JWT utilities
- `.github/workflows/ci.yml` — current CI workflow
- `app/modules/*/models/` — SQLModel model definitions for seed data
- `db/schema.sql` — schema orchestrator
- `db/schema/` — modular schema files
