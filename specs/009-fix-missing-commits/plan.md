# Implementation Plan: Fix Missing Session Commits

**Branch**: `main` (fixes directly on production branch) | **Date**: 2026-05-14 | **Spec**: specs/009-fix-missing-commits/spec.md
**Input**: Feature specification from `specs/009-fix-missing-commits/spec.md`

## Summary

16 write methods across 3 service files return 2xx success but never call `session.commit()` — all data is silently rolled back when the `get_session()` context closes. Fix by adding `session.commit()` + `session.refresh()` before each return. Also add persistence-verification tests and temporarily increase connection pool to reduce contention.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLModel, SQLAlchemy 2.0  
**Storage**: PostgreSQL via `get_session()` context manager (auto-rollback on close)  
**Testing**: pytest with TestClient, admin_headers (real Supabase JWT)  
**Target Platform**: Linux server (Leapcell)  
**Project Type**: Web service (REST API)  
**Performance Goals**: <80% pool utilization under peak concurrent load  
**Constraints**: Production system — fixes must be zero-downtime, no schema changes, no migrations  
**Scale/Scope**: 3 service files, ~16 methods to fix, ~5 new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Layer Separation**: Fixes live entirely in service layer — routers and repositories untouched. No violation.
- [x] **II. Stateless Pattern**: The fix adds `session.commit()` within existing `get_session()` blocks — keeps the stateless pattern intact. No violation.
- [x] **III. Typed Contracts**: No return type changes — methods still return the same DTOs/ORM models. No violation.
- [x] **IV. Domain Exceptions**: No exception handling changes — commit failures propagate naturally through the existing `get_session()` rollback. No violation.
- [x] **VI. Session Lifecycle**: The fix is precisely about respecting the documented session lifecycle — `get_session()` docstring says "Caller is responsible for commit." No violation.

**Gate result**: PASS — no constitution violations. The fix aligns with documented patterns.

## Project Structure

### Documentation (this feature)

```text
specs/009-fix-missing-commits/
├── plan.md              # This file
├── research.md          # Audit report & analysis
├── data-model.md        # Entity state transitions
├── quickstart.md        # Test scenarios
├── contracts/           # API contracts (unchanged)
├── audit-missing-commits.md  # Full audit report
└── tasks.md             # (/speckit.tasks command output)
```

### Source Code (repository root)

```text
app/modules/enrollments/services/
└── enrollment_service.py    # FIX: 5 methods

app/modules/competitions/services/
├── team_service.py          # FIX: 7 methods
└── competition_service.py   # FIX: 4 methods

tests/
├── test_academics_courses.py     # UPDATE: add persistence test
├── test_enrollments.py           # UPDATE: add persistence tests
└── test_competitions.py          # UPDATE: add persistence tests

app/db/
└── connection.py                 # TUNE: temporary pool_size increase
```

**Structure Decision**: Single project (Python FastAPI monolith). No structural changes.

## Complexity Tracking

> No constitution violations — section not required.

## Phase 0: Research

Research is complete — see `specs/009-fix-missing-commits/research.md` and the full audit at `specs/006-daily-report-fixes/audit-missing-commits.md`.

### Key findings

- Root cause: `get_session()` auto-rollbacks on close if no explicit `commit()`
- 16 methods affected across 3 service files
- Connection pool: one enrollment request opens 3 separate sessions → pool exhaustion risk
- Tests only check response body, never verify persistence

## Phase 1: Design

### Data Model

No schema changes. Entity state transitions documented in `data-model.md`.

### Contracts

No API contract changes. All endpoints return identical shapes. Contracts documented in `contracts/` for testing reference.

### Test Plan

1. **Enrollment persistence test**: Create enrollment → GET roster → verify student present
2. **Enrollment drop test**: Drop enrollment → GET enrollment → verify status
3. **Enrollment transfer test**: Transfer → verify source dropped + target created
4. **Team registration test**: Register team → GET teams → verify present
5. **Competition CRUD test**: Create competition → GET list → verify present
