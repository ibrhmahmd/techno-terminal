# Implementation Plan: Advanced User & Auth Management

**Branch**: `016-user-auth-management` | **Date**: 2026-05-20 | **Spec**: `specs/016-user-auth-management/spec.md`
**Input**: Feature specification from `/specs/016-user-auth-management/spec.md`

## Summary

Add five feature areas to the auth module: admin user management (list/read/update/deactivate users), self-service profile enhancement (change email, session/activity history), invite-based registration, session & security controls (active sessions, logout-all, MFA stub), and audit reporting (login history, password changes, failed attempts). New entities: `AuditLog` table, `User.email` field, `User.invite_token`/`.invite_expires_at`, and `User.deleted_at`. Two new services or extensions to `AuthService`. System admin role required for admin endpoints.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, SQLModel, Supabase Python SDK (auth), Pydantic v2
**Storage**: PostgreSQL (local User + new AuditLog table), Supabase Auth (credentials, sessions)
**Testing**: pytest, httpx (TestClient), unittest.mock for Supabase calls
**Target Platform**: Linux server (Leapcell deployment)
**Project Type**: Web service (REST API)
**Performance Goals**: NEEDS CLARIFICATION — pagination expectations for audit logs; TTL for invite tokens
**Constraints**: Must maintain backward compatibility. Admin endpoints guarded by `system_admin` role. Self-deactivation prevented. No hard-deletes; always soft-delete with Supabase identity cleanup.
**Scale/Scope**: 5 user stories, ~8 new endpoints, 1 new model (AuditLog), 3 User model extensions (email, invite fields, deleted_at), 2 new service areas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gate 1 — No `-> dict` / `-> list[dict]` / `-> tuple` in service/repository**: All new DTOs must be typed Pydantic models with `ConfigDict(from_attributes=True)`. AuditLog queries and paginated responses included. **PASS** (with vigilance).

**Gate 2 — No `from app.api.schemas` inversion in modules**: New service methods will use DTOs from `app/modules/auth/schemas/`. Routers will use `app/api/schemas/auth/` for HTTP-only shapes. **PASS**.

**Gate 3 — DTO naming convention**: Input DTOs follow `{Operation}{Entity}Input`. Output DTOs follow `{Entity}{Operation}Result`. Read models follow `{Entity}{Qualifier}DTO`. **PASS**.

**Gate 4 — Router concerns only**: Endpoints delegate to service methods. No business logic in routers. **PASS**.

**Gate 5 — Service layer pattern**: NEEDS CLARIFICATION — admin management could extend `AuthService` (stateless, own session) or create a separate `AdminAuthService`. Audit service could be separate or part of shared module. Resolve in Phase 0.

**Gate 6 — Dead code discipline**: Before migration, grep for callers of any refactored methods. Delete dead code immediately. **PASS** (reminder).

### Post-Design Re-Evaluation

*[To be filled after Phase 1]*

## Project Structure

### Documentation (this feature)

```text
specs/016-user-auth-management/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── admin-auth-api.md
```

### Source Code (repository root)

```text
app/
├── modules/
│   └── auth/
│       ├── models/
│       │   ├── auth_models.py         # Extend User: email, deleted_at, invite_token, invite_expires_at
│       │   └── audit_log.py           # NEW — AuditLog model
│       ├── schemas/
│       │   ├── auth_schemas.py        # Add admin DTOs, audit DTOs
│       │   └── __init__.py
│       ├── repositories/
│       │   ├── auth_repository.py     # Add list/update/soft-delete queries
│       │   └── audit_repository.py    # NEW — AuditLog CRUD
│       └── services/
│           ├── auth_service.py        # Extend: admin management methods, invite flow
│           └── audit_service.py       # NEW — audit logging service
├── api/
│   ├── schemas/
│   │   └── auth.py                    # Add admin HTTP DTOs, audit DTOs
│   ├── routers/
│   │   ├── auth_router.py             # Add self-service: change email, sessions, activity
│   │   └── admin_auth_router.py       # NEW — admin user management + audit endpoints
│   └── dependencies.py                # Add require_system_admin guard if missing
├── db/
│   └── migrations/
│       └── 063_user_auth_extensions.sql  # NEW migration: audit_log, user columns
tests/
└── test_auth.py                       # Add tests for all new endpoints
```

**Structure Decision**: Single project — extend existing auth module with new model, repository, and service files following the horizontal layer pattern (the auth module has ≤2 entities: User and AuditLog).

## Complexity Tracking

> No constitution violations expected. All changes follow existing patterns.

