# Implementation Plan: Testing Pipeline & CI/CD

**Branch**: `025-description-single-step` | **Date**: 2026-06-08 | **Spec**: `specs/026-testing-pipeline/spec.md`

## Summary

Set up a two-tier testing infrastructure: (1) local test database via `.env.test` for fast inner-loop development, and (2) a GitHub Actions CI pipeline that runs backend tests + frontend build validation in an isolated cloud environment on every push/PR. The `.env.test` file and config auto-detection already exist — this plan completes the remaining automation, documentation, and CI workflow wiring.

## Technical Context

**Language/Version**: Python 3.10+ (backend), TypeScript/React (frontend)  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic, Supabase (backend); React, Vite, TanStack Query (frontend)  
**Storage**: PostgreSQL 15+ (local dev database on `localhost:5432`)  
**Testing**: pytest (backend), npm run build / tsc (frontend validation)  
**Target Platform**: Linux (GitHub Actions runner), Windows (local dev)  
**Project Type**: Web service (backend) + SPA frontend — two separate repositories  
**Backend Path**: `E:\Users\Ibrahim\Desktop\techno_data_ Copy`  
**Frontend Path**: `E:\Users\Ibrahim\Desktop\techno_terminal_UI`  
**Performance Goals**: CI pipeline completes in under 10 minutes total; local test suite runs in under 2 minutes  
**Constraints**: Must never touch production database; must handle PostgreSQL-specific features (JSONB, TIMESTAMPTZ, PL/pgSQL triggers, custom enums) — SQLite in-memory is NOT acceptable  
**Scale/Scope**: ~23 existing test files; ~10 business modules; 70+ database migrations; 2 repositories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| No inverted dependencies | ✅ PASS | Testing infrastructure does not create new module code or import chains |
| No `-> dict` / loose return types | ✅ PASS | No new public service/repository methods introduced |
| Layer separation respected | ✅ PASS | CI config and test DB setup exist outside the Router/Service/Repository layers |
| Dead code discipline | ✅ PASS | New files only — no modification of existing module code |
| Auth-guarded endpoints | ✅ PASS | CI does not bypass auth; test fixtures use mock tokens already in `conftest.py` |

No constitution violations. This is infrastructure/testing setup, not a feature module.

## Project Structure

### Documentation (this feature)

```text
specs/026-testing-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 — resolved unknowns
├── data-model.md        # Phase 1 — test DB schema & env config
├── quickstart.md        # Phase 1 — how to run tests locally + CI
├── contracts/           # Phase 1 — CI workflow contract
└── tasks.md             # Phase 2 — task breakdown (created by /speckit.tasks)
```

### Source Code (repository root — backend)

```text
.
├── .env.test                     # EXISTS — test env config (local DB)
├── .github/workflows/ci.yml      # TO CREATE — GitHub Actions CI pipeline
├── app/core/config.py            # EXISTS — auto-detects .env.test via PYTEST_CURRENT_TEST
├── tests/
│   ├── conftest.py               # EXISTS — fixtures: client, tokens, db_session
│   ├── test_crm.py               # EXISTS
│   └── ... (22 other test files)
├── db/
│   ├── schema/                   # 17 modular SQL files
│   ├── schema.sql                # Full schema apply script
│   └── migrations/               # 70+ migration files
└── scratch/                      # Cleanup scripts (apply migrations, schema sync)
```

### Source Code (frontend — separate repo at `techno_terminal_UI/`)

```text
.
├── src/                          # TypeScript/React source
├── package.json                  # npm scripts: build, lint, test
└── node_modules/
```

## Phase 0 — Research (resolve unknowns)

### Unknown 1: CI test credentials for Supabase

**Decision**: Use mock JWT tokens in CI (existing `tests/utils/jwt_mocks.py` with HS256 + `TEST_SECRET`). No real Supabase project needed — the `override_auth` fixture bypasses Supabase validation entirely. Supabase URL/anon key in `.env.test` can remain as-is since no tests hit real Supabase endpoints.

### Unknown 2: Twilio/Gmail in CI

**Decision**: Mock all dispatchers. The existing `tests/utils/` should get notification mock helpers that prevent actual SMS/email sending during tests. CI environment can use dummy values (`TEST_` prefixed or empty strings) — the dispatchers will be patched.

### Unknown 3: Frontend test scope in CI

**Decision**: CI validates `npm run build` (TypeScript compilation + Vite build). Unit testing (vitest) is deferred — the spec's US3 covers build validation only. Can be upgraded later.

## Phase 1 — Design & Artifacts

### Artifact: `data-model.md`

Documents the test environment configuration schema — what each `.env.test` variable maps to and how it differs from production.

### Artifact: `contracts/ci-workflow.md`

Defines the CI workflow contract:
- Trigger: `push` + `pull_request` to any branch
- Job 1 — Backend Tests: Ubuntu runner → PostgreSQL 15 service container → schema init → pytest
- Job 2 — Frontend Build: Ubuntu runner → Node 18 → npm ci → npm run build
- Environment variables: `DATABASE_URL` set to CI service container; mock values for Supabase/Twilio/Gmail

### Artifact: `quickstart.md`

Step-by-step for developers:
1. Ensure local PostgreSQL is running
2. Run `psql -f db/schema.sql` against local DB
3. Apply migrations in chronological order
4. Run `pytest tests/ -v` (auto-loads `.env.test`)
5. Frontend: `cd ../techno_terminal_UI && npm run build`

### Agent Context Update

After Phase 1 artifacts are created, update `AGENTS.md` Speckit reference to point to `specs/026-testing-pipeline/plan.md`.
