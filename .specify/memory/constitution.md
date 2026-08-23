<!--
## Sync Impact Report
Version change: 1.1.1 → 1.1.2 (PATCH)

### Changes
- §V Auth-Guarded Endpoints: CORRECTED the documented role mechanism to match code
  truth. The previous text claimed the user role is read from JWT `app_metadata.role`;
  in reality the JWT only proves identity (Supabase uid mapped to a local User row via
  `get_user_by_supabase_uid`) and authorization reads exclusively from the local
  `users.role` column (`app/api/dependencies.py:100-106`). Mock-token guidance updated:
  tests need a matching seeded local user row or the `override_auth` fixture, not a
  role claim. Also listed `require_system_admin`, which was missing from the guard list.
- Operational Constraints / Database Engine Configuration: corrected `sslmode=require`
  → `sslmode=prefer` per `app/db/connection.py:28`.
- Development Workflow / Database Migrations: schema file count corrected 17 → 18;
  duplicate-prefix list extended with 051 and 057; total migration count noted as 87.

### Templates requiring updates
- .specify/templates/plan-template.md ✅ No change needed (no stale references found)
- .specify/templates/spec-template.md ✅ No change needed (no stale references found)
- .specify/templates/tasks-template.md ✅ No change needed (no stale references found)
- .specify/templates/commands/*.md ✅ No change needed (grep for `app_metadata` matched
  only this file)

### Deferred items
- None

Source audit: feature 039-audit-employee-creation findings F-11 (accepted-risk) and
post-analysis remediation R-batch C1.
-->

# Techno Terminal Constitution

## Core Principles

### I. Router → Service → Repository Layer Separation

Every module follows a strict three-layer architecture. Routers (in `app/api/routers/`)
handle HTTP concerns — validation via Pydantic, dependency injection via `Depends()`, and
nothing else. Services (in `app/modules/*/services/`) own all business logic and transaction
boundaries. Repositories (in `app/modules/*/repositories/`) contain only pure SQL/SQLModel
queries — zero business rules. No layer may skip the one below it.

- Services MUST NOT import from `app.api.*` (inverted dependency)
- Repositories MUST NOT contain business rules, validation, or orchestration
- Routers MUST NOT contain SQL queries or business logic
- **Two-Layer Schema Rule**: DTOs live in the slice that owns them. `app/api/schemas/`
  only contains API-specific shapes that differ from service output. Services MUST NOT
  import from `app.api.schemas.*`

### II. Module Organization — Vertical Slices (D+ Hybrid for Complex Entities)

Modules with ≤2 entities use flat Horizontal Layer (Pattern A). Modules with a dominant
entity and ≥3 distinct workflow concerns use the D+ Hybrid pattern — the entity becomes a
namespace with sub-slices (`core/`, `directory/`, `lifecycle/`, `analytics/`, etc.). Models
stay horizontal (shared `models/` directory per module) regardless of slice structure —
SQLModel entities are registered with the ORM at import time and must not be duplicated
across slices.

- `models/` is always horizontal, never per-slice
- Every slice directory contains exactly: `__init__.py`, `interface.py`, `service.py`,
  `repository.py`, `schemas.py`
- **Interface design**: `@runtime_checkable` Protocol classes named
  `{Entity}{Concern}Interface` (never `I`-prefix, never `Protocol` suffix). Method bodies
  are `...`. Every public service method MUST appear in the interface.
- **Import dependency chain** (prevents circular imports):
  `interface.py` → can import from `schemas.py`, `models/`
  `schemas.py` → can import from `models/`, shared constants
  `repository.py` → can import from `models/`, constants, shared
  `service.py` → can import from `repository.py`, `schemas.py`, `interface.py`, helpers,
  constants, and other slices' schemas (NOT other slices' services)
- **Cross-slice dependency**: Repositories CAN be imported across slices (they are
  stateless query functions). Services MUST NOT import other services within the same
  module — cross-slice orchestration goes through the module root `__init__.py`.

### III. Typed Contracts — No Loose Return Types

Every public service or repository method returns a typed Pydantic DTO or an ORM model.
Bare `dict`, `list[dict]`, and `tuple` return types are forbidden at public method
boundaries — they bypass validation, hide structure changes, and accumulate tech debt.
All DTOs receiving ORM data MUST set `model_config = ConfigDict(from_attributes=True)`.

- `-> dict`, `-> list[dict]`, `-> tuple` are prohibited in public service and repository
  method signatures (i.e., any method declared in the slice `interface.py` Protocol)
- Every public return type must be a named model or DTO class
- **Private helper exception**: Repository module-internal helper functions (not appearing
  in any Protocol interface) MAY return `tuple[list[DTO], int]` for `(rows, total)` pairs,
  provided the calling service wraps the result in a named DTO before the value crosses a
  public boundary
- Input DTOs: `{Operation}{Entity}Input`
  Output DTOs: `{Entity}{Operation}Result`
  Read models: `{Entity}{Qualifier}DTO`

### IV. Response Envelope & Domain Exception Mapping

Every API response uses the standard envelope:
`{"success": bool, "data": ..., "message": ..., "error": ...}`. Services must raise typed
domain exceptions instead of generic `ValueError` or `HTTPException`. Exception handlers
in `app/api/exceptions.py` map:

- `NotFoundError` → 404
- `ValidationError` → 422
- `BusinessRuleError` → 409
- `ConflictError` → 409
- `AuthError` → 401

Pydantic `RequestValidationError` is also caught and returned as 422 with the standard
envelope.

### V. Auth-Guarded Endpoints

All endpoints except health checks (`/health`, `/kaithhealthcheck`) require a valid
Supabase JWT. Auth flows through `get_current_user()` in `app/api/dependencies.py` which
validates the JWT via `get_supabase_anon()` and maps the Supabase uid to the local `User`
model. The JWT proves identity ONLY — authorization never reads role claims.

The user role is read exclusively from the local `users.role` column
(`dependencies.py:100-106`). Role guards enforce access:

- `require_admin`: allows `admin` + `system_admin`
- `require_system_admin`: allows `system_admin` only
- `require_any`: any authenticated active user — use for read endpoints serving all staff

Inactive accounts are rejected with 403 before any role check.

Mock test JWTs use HS256 with `TEST_SECRET`. Because roles come from the database, a
mock token MUST be paired with either a matching seeded local user row (same
`supabase_uid`) or the `override_auth` fixture, which replaces `get_current_user`
entirely — role claims inside mock tokens are not authoritative.

## Operational Constraints

### Database Engine Configuration

Actual values from `app/db/connection.py` (code is the source of truth):

- Pool: `pool_size=10`, `max_overflow=5` (15 max total), `pool_timeout=30`
- Health: `pool_pre_ping=True`, `pool_recycle=240` (4 minutes)
- SSL: `sslmode=prefer`
- Timeout: `statement_timeout=30000` (30 seconds global)
- Session: `expire_on_commit=False`
- TCP keepalive: `keepalives=1`, idle=30s, interval=10s, count=5

### Session Lifecycle & Unit of Work Rules

Two DI patterns coexist and MUST NOT be confused:

1. **UoW-based** (CRM, Finance, HR, Enrollments): The session is injected via `get_db()`
   Depends. The session lifecycle (open/commit/close) is managed by FastAPI's `get_db()`
   generator — NOT by the UnitOfWork. The UoW only owns the session when used standalone
   via `with UnitOfWork():`.

2. **Stateless** (Academics, Attendance, Competitions, Analytics): Services create their
   own internal sessions via `get_session()`.

**UoW Rollback Constraint**: `get_db()` calls `session.commit()` on normal generator
exit. If a service calls `uow.rollback()` without re-raising an exception, `get_db()` will
still `commit()` afterward. This can commit data that was intentionally rolled back.
Services MUST let exceptions propagate after rollback, or avoid calling `uow.rollback()`
when the session is owned by `get_db()`.

**Notification Service**: `get_notification_service()` always opens its own independent
session via `get_session()` — it receives a different database session from the rest of
the request. This is intentional for background/non-transactional notifications.

### Router Registration Order

`group_directory_router` MUST be registered before `groups_router` — otherwise
`/{group_id}` shadows `/enriched`. Within `group_directory_router`, static routes (e.g.,
`/filter`, `/enriched`) MUST be declared before parameterized routes (e.g.,
`/{group_id}`) to prevent path-shadowing.

## Development Workflow

### Database Migrations

- Schema: 18 modular files in `db/schema/` applied in dependency order via `db/schema.sql`
- Migrations: 87 numbered `NNN_description.sql` files in `db/migrations/`, apply in
  chronological order (not strictly numeric — some numbers have duplicates from parallel
  branches: 008, 020, 021, 022, 026, 030, 036, 051, 057)

### Testing & Tokens

- Real Supabase JWTs expire ~1 hour. Regenerate via `python scripts/get_test_jwt.py` and
  update `admin_token` in `tests/conftest.py`
- Mock `system_admin` tokens are generated via `tests/utils/jwt_mocks.py` using HS256 with
  a hardcoded `TEST_SECRET` — use these for tests that don't need real Supabase

### Dead Code Discipline

Before any refactoring or migration, run the full dead code audit: grep for callers of
every method. Delete dead code immediately — never migrate it into a new structure. Zero
tolerance for commented-out code, deprecated methods kept for "backward compatibility," or
subset methods superseded by broader equivalents.

## Governance

The constitution supersedes all other development practices when conflicts arise.
Amendments require:

1. Document the proposed change with rationale
2. Update version according to semver (MAJOR: incompatible principle change, MINOR: new
   principle, PATCH: clarification)
3. Record the amendment date

`/speckit.plan` and `/speckit.analyze` both validate against this constitution.
Constitution violations are always CRITICAL and must be resolved before implementation
proceeds.

**Version**: 1.1.2 | **Ratified**: 2026-05-11 | **Last Amended**: 2026-08-23
