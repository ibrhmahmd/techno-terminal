# Implementation Plan: Self-Service Auth Features

**Branch**: `015-self-service-auth` | **Date**: 2026-05-20 | **Spec**: `specs/015-self-service-auth/spec.md`
**Input**: Feature specification from `/specs/015-self-service-auth/spec.md`

## Summary

Add three self-service endpoints to the auth module: change password (verify current + set new via Supabase admin API), forgot password (trigger Supabase reset email), and update profile (PATCH username). All guarded by `get_current_user`. AuthService remains stateless. No new models or migrations needed.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, SQLModel, Supabase Python SDK (auth), Pydantic v2  
**Storage**: PostgreSQL (local User table), Supabase Auth (credentials, sessions)  
**Testing**: pytest, httpx (TestClient), unittest.mock for Supabase calls  
**Target Platform**: Linux server (Leapcell deployment)  
**Project Type**: Web service (REST API)  
**Performance Goals**: N/A — 3 lightweight endpoints, no new queries beyond existing patterns  
**Constraints**: Must maintain backward compatibility. Username update does NOT update Supabase email identity. Deactivated users blocked via 403.  
**Scale/Scope**: 3 endpoints, ~3-4 files modified, 1 new DTO file, 1 test file updated.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gate 1 — No `-> dict` / `-> list[dict]` / `-> tuple` in service/repository**: All new DTOs will be typed Pydantic models accepting `ConfigDict(from_attributes=True)` where applicable. **PASS**

**Gate 2 — No `from app.api.schemas` inversion in modules**: New service methods will use DTOs from `app/modules/auth/schemas/`. Router will use `app/api/schemas/auth/` for HTTP-only shapes. Services will NOT import from `app.api.schemas`. **PASS**

**Gate 3 — DTO naming convention**: Input DTOs follow `{Operation}{Entity}Input` pattern (e.g., `ChangePasswordInput`). Existing `UserPublicDTO` used for profile output. **PASS**

**Gate 4 — Router concerns only**: Endpoints will delegate to `AuthService` methods. No business logic in routers. **PASS**

**Gate 5 — AuthService is stateless**: Opens own session via `get_session()`. Consistent with existing pattern. **PASS**

### Post-Design Re-Evaluation

All gates remain **PASS** after Phase 1 design. Research.md resolves all unknowns. Data model confirms no entity changes. Contracts define clean API shapes. No new constitution violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/015-self-service-auth/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (no entity changes)
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── auth-api.md
```

### Source Code (repository root)

```text
app/
├── modules/
│   └── auth/
│       ├── schemas/
│       │   └── auth_schemas.py   # Add ChangePasswordInput, ForgotPasswordInput, UpdateProfileInput
│       └── services/
│           └── auth_service.py   # Add change_password, forgot_password, update_profile methods
├── api/
│   ├── schemas/
│   │   └── auth.py               # Add HTTP request DTOs (proxy to module DTOs or extend)
│   └── routers/
│       └── auth_router.py        # Add 3 new endpoint functions
tests/
└── test_auth.py                  # Add test classes for all 3 endpoints + error paths
```

**Structure Decision**: Single project — extend existing auth module files. No new directories.

## Complexity Tracking

> No constitution violations in this plan. All changes follow existing patterns. N/A.
