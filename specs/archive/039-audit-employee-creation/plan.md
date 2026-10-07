# Implementation Plan: Employee Creation Endpoint Audit & Fixes

**Branch**: `039-audit-employee-creation` | **Date**: 2026-08-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/039-audit-employee-creation/spec.md`

## Summary

Systematic audit and repair of the staff onboarding path (`POST /hr/employees`, `PUT /hr/employees/{id}`, `POST /hr/employees/{id}/create-account`, `GET /hr/staff-accounts`). Investigation already confirmed concrete defects: duplicate checks short-circuit on the first collision, Supabase failures are misreported as conflicts, midway failures orphan remote auth users, concurrent inserts hit unhandled unique-constraint violations (500s), update-path normalization can violate a DB CHECK, and the accounts overview ships permanent blank fields. Work is defect-fixing within the existing HR horizontal layers plus a findings catalog and per-defect regression tests — no new modules, no schema changes (DB UNIQUE constraints already exist).

## Technical Context

**Language/Version**: Python 3.10+ (repo venv runs 3.13)
**Primary Dependencies**: FastAPI, SQLModel/SQLAlchemy, supabase-py (auth admin API), Pydantic v2
**Storage**: PostgreSQL 15 (Supabase-hosted), SQLModel ORM, pool per `app/db/connection.py`
**Testing**: pytest + FastAPI TestClient; auth via `override_auth` fixture + HS256 mock JWTs (`tests/utils/jwt_mocks.py`)
**Target Platform**: Linux server (Leapcell/Railpack)
**Project Type**: Web service (REST API backend)
**Performance Goals**: Staff endpoints respond < 200ms p95 under normal load (repo precedent from plan 038)
**Constraints**: Zero partial state on failure; UoW rollback constraint (constitution §Operational); no destructive data changes; typed domain exceptions only in services; no hard deletes
**Scale/Scope**: ~20 employees, ~500 tasks steady state; 4 endpoints in scope; 1 findings catalog + regression suite

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| I. Router → Service → Repository separation | ✅ PASS | All fixes stay in HR service/repository layers; routers remain HTTP-only (error translation only). |
| II. Module organization (HR = horizontal Pattern A) | ✅ PASS | No new slices. Public method signature changes (e.g., new repo methods for FR-011) MUST be added to `services/interface.py` / `repositories/interface.py` Protocols with `{Entity}{Concern}Interface` naming. |
| III. Typed contracts | ✅ PASS | New/extended DTOs named per convention (`StaffAccountsListResult` style if needed); `from_attributes=True` on ORM-fed DTOs; no `-> dict`/`-> tuple` introduced at public boundaries. Existing private `(rows, total)` helper stays repository-internal. |
| IV. Response envelope & exception mapping | ✅ PASS | All new failures raised as typed domain exceptions (`ConflictError`/`ValidationError`/`BusinessRuleError`); `IntegrityError` translated in service layer, never leaked raw. |
| V. Auth-guarded endpoints | ✅ PASS | Guards untouched (`require_admin` on all four endpoints). |
| Operational: UoW rollback constraint | ⚠️ ATTENTION | Services currently call `uow.commit()` mid-operation while the session is owned by `get_db()`. Fixes MUST let exceptions propagate after rollback (never swallow), and failure paths must roll back before raising so `get_db()` cannot commit partial work. See research D5/D6. |
| Dead Code Discipline | ⚠️ ATTENTION | Audit confirmed dead code to delete during fixes: `EmployeeCrudService._normalize_update_employment_data` (never called), likely-unused `app/modules/hr/validators/employee_validators.py`, duplicate model-level `EmployeeCreate`/`EmployeeRead` DTOs — grep for callers before deletion (task-phase verification). |

**Gate result**: PASS — two attention items are addressed by explicit design decisions (research D5–D7, D11).

## Project Structure

### Documentation (this feature)

```text
specs/039-audit-employee-creation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md          # Phase 1 output (/speckit.plan command)
├── frontend-migration-notes.md  # Client-facing change list for frontend devs
├── contracts/             # Phase 1 output (/speckit.plan command)
│   └── hr-staff-api.md  # Contracts for the 4 in-scope endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── routers/hr_router.py            # Error translation only; drop None-placeholder mapping
│   └── dependencies.py                 # Untouched (guards/factories)
├── modules/hr/
│   ├── models/employee_models.py       # Employee entity (audit: remove dead DTOs if uncalled)
│   ├── repositories/
│   │   ├── employee_repository.py      # find_by_* probes; no business rules
│   │   ├── staff_account_repository.py # + user-status linkage method (FR-011)
│   │   ├── interface.py                # Protocol updates for any new repo methods
│   │   └── unit_of_work.py             # HRUnitOfWork (unchanged surface)
│   ├── services/
│   │   ├── employee_crud_service.py    # Aggregate duplicate checks; update-path fix; deactivation hook
│   │   ├── staff_account_service.py    # Failure classification + Supabase compensation
│   │   └── interface.py               # Protocol updates for changed public methods
│   ├── schemas/                        # Extended staff-account read DTOs (FR-010)
│   └── constants.py                    # Single source for field limits (dead constants resolved)
├── shared/constants.py                 # MIN_PASSWORD_LENGTH=12 kept (≥8 spec minimum satisfied)
└── shared/exceptions.py                # Typed hierarchy (unchanged)

db/migrations/                          # NO new migrations expected (UNIQUE constraints exist)
tests/
├── test_hr.py                          # Existing endpoint tests (extend)
├── test_hr_full.py                     # Existing CRUD/staff-account tests (extend)
└── test_hr_audit_regressions.py        # NEW: per-defect regression tests (FR-013)
```

**Structure Decision**: Fix-in-place within the HR module's existing horizontal layers (constitution Pattern A). The findings catalog lives at `specs/039-audit-employee-creation/findings.md` (documentation artifact, produced during implementation). Regression coverage lands in a dedicated `tests/test_hr_audit_regressions.py` so each cataloged defect maps to an executable check (FR-013).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none — gates pass) | | |
