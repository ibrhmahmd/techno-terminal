# Implementation Plan: Auth Module Bug Fixes & Audit Remediation

**Branch**: `014-auth-audit-fixes` | **Date**: 2026-05-20 | **Spec**: `specs/014-auth-audit-fixes/spec.md`
**Input**: Feature specification from `/specs/014-auth-audit-fixes/spec.md`

## Summary

Fix 42 audit findings in the auth module across 6 categories: runtime bugs (orphaned Supabase identities, email leakage, unreachable code), security edge cases (password reset on inactive users), dead code removal, constitution violations (dict types, direct imports, missing DTO configs), missing test coverage, and minor hardening (enum usage, error logging). All changes are in the auth module and its tests — no data model changes, no new endpoints, no breaking API changes.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, SQLModel, Supabase Python SDK (auth), Pydantic v2  
**Storage**: PostgreSQL (via SQLModel/SQLAlchemy), Supabase Auth (external)  
**Testing**: pytest, httpx (TestClient), mock JWT tokens (HS256)  
**Target Platform**: Linux server (Leapcell deployment)  
**Project Type**: Web service (REST API)  
**Performance Goals**: N/A — bug-fix/cleanup feature, no new endpoints. Existing performance characteristics are unchanged.  
**Constraints**: Must maintain backward compatibility — no breaking API contract changes, no DB migrations required.  
**Scale/Scope**: 1 module (auth), ~6 files modified + 1 test file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gate 1 — No `-> dict` / `-> list[dict]` / `-> tuple` in service/repository layers**: The spec specifically fixes this (FR-004). Currently `create_user` accepts `dict` — this will be changed to typed DTO. **PASS**

**Gate 2 — No `from app.api.schemas` inversion in modules**: Already clean — zero current violations. The fix only removes dead code and fixes import paths. **PASS**

**Gate 3 — Dead code discipline**: Phase 0 includes mandatory dead code deletion (`get_users_for_employee`, `update_user`, `PasswordResetBody`, `UserRead`). **PASS**

**Gate 4 — DTOs must have `model_config = ConfigDict(from_attributes=True)`**: Spec explicitly requires this (FR-007). **PASS**

**Gate 5 — Services imported from module root, not internal paths**: Spec requires fixing `auth_router.py:31` and `dependencies.py:121` to import `AuthService` from `app.modules.auth`. **PASS**

**Gate 6 — No constitution violations in the plan itself**: No violations. The plan is entirely about compliance. **PASS**

**Gate 7 — All 42 findings resolved**: Per SC-001. Research.md + data-model.md confirm completeness. **PASS**

### Post-Design Re-Evaluation

All gates remain **PASS** after Phase 1 design. No new constitution violations introduced. The design artifacts (data-model.md, contracts/, quickstart.md) confirm:
- Zero `-> dict` types remain in repo
- Zero `from app.api.schemas` inversions exist
- All 4 dead code items identified for deletion
- DTO ConfigDict fix confirmed
- Import path fixes confirmed
- No new violations introduced

## Project Structure

### Documentation (this feature)

```text
specs/014-auth-audit-fixes/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no entity changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (minimal — no API contract changes)
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # (/speckit.tasks command - not created by /speckit.plan)
```

### Source Code (repository root)

```text
app/
├── modules/
│   └── auth/
│       ├── __init__.py              # Remove dead aliases + exports
│       ├── constants.py             # No changes
│       ├── models/
│       │   └── auth_models.py       # Fix is_admin property
│       ├── schemas/
│       │   ├── __init__.py          # Remove dead DTOs
│       │   └── auth_schemas.py      # Remove dead DTOs, add ConfigDict, fix naming
│       ├── repositories/
│       │   ├── __init__.py          # Remove update_user
│       │   └── auth_repository.py   # Remove update_user, fix create_user signature
│       └── services/
│           ├── __init__.py          # No changes
│           └── auth_service.py      # Remove get_users_for_employee, add orphan cleanup, add inactive check
├── api/
│   ├── dependencies.py              # Fix AuthService import path
│   └── routers/
│       └── auth_router.py           # Fix AuthService import, remove debug prints, fix logout error handling
tests/
└── test_auth.py                     # Add tests for login, create_user, refresh, logout, reset-password; fix broken tests
```

**Structure Decision**: Single project (existing structure). All changes are within existing files — no new directories or files needed.

## Complexity Tracking

> No constitution violations in this plan. All changes are in direct service of constitution compliance. N/A.
