# Implementation Plan: Employee Soft Delete with Restore & Re-hire

**Branch**: `040-employee-soft-delete` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/040-employee-soft-delete/spec.md`

## Summary

Add admin-facing soft deletion for employees: `DELETE /hr/employees/{id}` stamps `deleted_at`/`deleted_by` and auto-blocks the linked login account in one transaction; `POST /hr/employees/{id}/restore` clears the markers with field-named conflict rejection when a re-hire occupies the identity; `GET /hr/employees?include_deleted=true` exposes deleted records for discovery. A migration adds the two columns and converts the three identity UNIQUE constraints into same-named partial unique indexes (`WHERE deleted_at IS NULL`) so deleted records never block re-hiring. No rows are ever physically removed; historical references (tasks, instructor/coach links, time logs) remain untouched.

## Technical Context

**Language/Version**: Python 3.10+ (repo venv runs 3.13)
**Primary Dependencies**: FastAPI, SQLModel/SQLAlchemy, PostgreSQL partial unique indexes, Pydantic v2
**Storage**: PostgreSQL 15+ (Supabase-hosted; live catalog verified during research), SQLModel ORM
**Testing**: pytest + FastAPI TestClient; `override_auth` + HS256 mock JWTs; new `tests/test_hr_delete.py`
**Target Platform**: Linux server (Leapcell/Railpack)
**Project Type**: Web service (REST API backend)
**Performance Goals**: Delete/restore respond < 200ms p95 (single-row transaction); list flag adds no measurable overhead at ~20 employees scale
**Constraints**: Zero hard deletes anywhere; UoW rollback constraint (constitution §Operational); typed domain exceptions only in services; routers HTTP-only; same-named index swap preserves F-04 IntegrityError mapper signals
**Scale/Scope**: ~20 employees steady state; 2 new endpoints + 1 query flag on an existing endpoint; 1 migration; schema files synced

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| I. Router → Service → Repository separation | ✅ PASS | New routes delegate to `EmployeeCrudService`; repo owns column mutations and probe filters; routers stay HTTP-only (no try/except translation — global typed handlers per 039 convention). |
| II. Module organization (HR = horizontal Pattern A) | ✅ PASS | No new slices/modules. New repo methods (`soft_delete`, `restore`) declared in BOTH `repositories/interface.py` and consumed via service Protocol per `{Entity}{Concern}Interface` rules. |
| III. Typed contracts | ✅ PASS | No tuples at public boundaries (R-3 patterns reused): delete returns envelope `data: bool`; restore returns `EmployeeReadDTO`; `include_deleted` extends existing typed list DTO with optional `deleted_at`/`deleted_by`. |
| IV. Response envelope & exception mapping | ✅ PASS | `NotFoundError`→404 (missing/double-delete), `ConflictError`→409 (restore collisions), `BusinessRuleError`→409 reserved; no raw IntegrityError leaks (mapper unchanged thanks to same-name index swap). |
| V. Auth-Guarded Endpoints | ✅ PASS | All three surfaces `Depends(require_admin)`; role read from local `users.role` per constitution v1.1.2 §V. |
| Operational: UoW rollback constraint | ✅ PASS | Delete = fetch → `set_user_active(False)` → stamp columns → single `uow.commit()`; exceptions propagate after rollback (F-02/F-03 pattern). Restore identical shape minus account step. |
| Dead Code Discipline | ✅ PASS | No superseded methods introduced; duplicate probes are modified in place (filters added), not duplicated. |

**Gate result**: PASS — no violations requiring complexity tracking.

## Project Structure

### Documentation (this feature)

```text
specs/040-employee-soft-delete/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Clarified specification (FR-001..FR-014)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── hr-employee-lifecycle-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
db/
├── migrations/
│   └── 079_employee_soft_delete.sql     # NEW: columns + constraint→partial-index swap
└── schema/
    ├── 02_tables_core.sql               # SYNC: employees table gains deleted_at/deleted_by
    └── 20_indexes.sql                   # SYNC: three uniques become partial (same names)

app/
├── api/
│   ├── routers/hr_router.py             # DELETE /{id}, POST /{id}/restore, include_deleted Query param
│   └── dependencies.py                  # Untouched (require_admin already returns current_user)
└── modules/hr/
    ├── models/employee_models.py        # Employee += deleted_at/deleted_by (FK users.id)
    ├── repositories/
    │   ├── employee_repository.py       # get_by_* filters; soft_delete(); restore(); list branch
    │   ├── staff_account_repository.py  # overview JOIN excludes deleted employees
    │   └── interface.py                 # Protocol additions (both interfaces as needed)
    ├── services/
    │   └── employee_crud_service.py     # delete_employee(); restore_employee(); list flag plumbing;
    │                                    # restore-collision probes reuse _validate_unique_fields
    └── schemas/employee_schemas.py      # EmployeeReadDTO += optional deleted_at/deleted_by

tests/
├── test_hr_delete.py                    # NEW: full lifecycle suite (delete/hide/block/rehire/restore)
└── test_hr_audit_regressions.py         # EXTEND: duplicate probes ignore deleted rows (FR-007 lock)
```

**Structure Decision**: Fix-in-place within HR's horizontal layers (constitution Pattern A). The feature touches exactly one module plus shared schema artifacts; no new modules, slices, or cross-module sweeps — dependent views keep rendering historical references because soft delete leaves all referencing rows intact.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none — gates pass) | | |
