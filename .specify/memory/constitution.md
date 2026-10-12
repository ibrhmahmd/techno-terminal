<!--
## Sync Impact Report
Version change: 1.1.2 → 2.0.0 (MAJOR)

### Changes
- §I and §II rewritten to the modular monolith recorded in docs/adr (ADR-0001–0010), which
  the architecture migration (epic #9) completed: routers live in each module's `api/`,
  `app/api/` keeps only shared HTTP code, modules follow a fixed order and talk through
  facades. The per-slice `interface.py` Protocol rule is removed (ADR-0008: a Protocol
  exists only where two adapters exist).
- §III: "public method" no longer means "declared in a slice Protocol".
- Session Lifecycle rewritten to ADR-0001/0009: one injected UnitOfWork per use case;
  `get_db()`, per-service `get_session()` and the self-sessioned notification service are gone.
- Testing & Tokens: paths follow the colocated test layout (#109).
-->

# Techno Terminal Constitution

## Core Principles

### I. Modular Monolith — the ADRs Are the Architecture

`app/` is a modular monolith. The binding rules are the ADRs in `docs/adr/` (0001–0010 and
later); where this constitution and an ADR disagree, the ADR wins. In short:

- Eleven modules in a fixed order, bottom to top: auth, hr, crm, academics, enrollments,
  attendance, competitions, finance, tasks, notifications, analytics (ADR-0003). A module
  imports only lower modules, and only through their facade (`app/modules/<m>/__init__.py`);
  any module may read any model, but writes only its own tables (ADR-0004).
- Inside a module, layers point downward: `api/ → services/ → repositories/ → schemas/,
  models/` (ADR-0002). Routers, HTTP schemas and dependency factories live in the module's
  `api/`; `app/api/` holds only shared HTTP code (`main.py`, `deps.py`, `exceptions.py`,
  the envelope schema).
- Routers handle HTTP only; services own business rules; repositories hold pure queries
  (raw SQL only in repositories). Services MUST NOT import a router's request/response
  schemas.
- A write workflow spanning modules lives in the highest module involved (ADR-0006).
- `pytest tests/architecture` enforces the order, facades, layers and the UoW rule, and
  pins the OpenAPI spec. A violation fails the suite.

### II. Module Organization

- Each module uses the same horizontal layers (ADR-0002); there are no per-entity
  sub-slices.
- `models/` is always horizontal, never per-slice: SQLModel entities register with the ORM
  at import time and must not be duplicated.
- A Protocol/ABC exists only where two adapters satisfy it; a test fake counts (ADR-0008).
  Notifier ports are the main example (ADR-0007).
- A service calls a sibling service only through the shared injected UnitOfWork; services
  never build their own dependencies or sessions (ADR-0009).
- Format checks are Pydantic validators on schemas; checks that need the database or
  business state live in services; there is no `validators/` layer (ADR-0010).

### III. Typed Contracts — No Loose Return Types

Every public service or repository method returns a typed Pydantic DTO or an ORM model.
Bare `dict`, `list[dict]`, and `tuple` return types are forbidden at public method
boundaries — they bypass validation, hide structure changes, and accumulate tech debt.
All DTOs receiving ORM data MUST set `model_config = ConfigDict(from_attributes=True)`.

- `-> dict`, `-> list[dict]`, `-> tuple` are prohibited in public service and repository
  method signatures
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
Supabase JWT. Auth flows through `get_current_user()` in `app/api/deps.py` which
validates the JWT via `get_supabase_anon()` and maps the Supabase uid to the local `User`
model. The JWT proves identity ONLY — authorization never reads role claims.

The user role is read exclusively from the local `users.role` column
(`app/api/deps.py`). Role guards enforce access:

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

### Session Lifecycle & Unit of Work Rules (ADR-0001, ADR-0009)

- Every use case runs in **one** injected `UnitOfWork` (`get_uow` / `UoW` in
  `app/api/deps.py`, built on `app/db/uow.py`). Services receive it; they never call
  `get_session()` or open their own sessions.
- Only the top-level use case commits, and it commits **before** external I/O.
- Notifications go through each module's Notifier port and run **after** the commit
  (ADR-0007); notifier failures are logged and never fail the request. Background
  notification work opens a fresh session inside `notifications/adapters/` only.
- A rollback must re-raise: never swallow an exception after rolling back.

### Router Registration Order

`group_directory_router` MUST be registered before `groups_router` — otherwise
`/{group_id}` shadows `/enriched`. Within `group_directory_router`, static routes (e.g.,
`/filter`, `/enriched`) MUST be declared before parameterized routes (e.g.,
`/{group_id}`) to prevent path-shadowing.

## Development Workflow

### Database Migrations

- Schema: 18 modular files in `db/schema/` applied in dependency order via `db/schema.sql`
- Migrations: numbered `NNN_description.sql` files in `db/migrations/`, apply in
  chronological order (not strictly numeric — some numbers have duplicates from parallel
  branches: 008, 020, 021, 022, 026, 030, 036, 051, 057)

### Testing & Tokens

- Real Supabase JWTs expire ~1 hour. Regenerate via `python scripts/get_test_jwt.py` and
  export it as `TEST_ADMIN_JWT` (read by the `admin_token` fixture in `app/conftest.py`)
- Mock `system_admin` tokens are generated via `app/testing/jwt_mocks.py` using HS256 with
  a hardcoded `TEST_SECRET` — use these for tests that don't need real Supabase
- Tests live with the code they test (`app/modules/<m>/tests/`, `app/db/tests/`, ...);
  shared fixtures in `app/conftest.py`; only repo-wide contracts in `tests/architecture/`
- Tests that write use the `uow` / `client_with_uow` fixtures (SAVEPOINT, rolled back) and
  run against the local Postgres container, never production

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

**Version**: 2.0.0 | **Ratified**: 2026-05-11 | **Last Amended**: 2026-10-12
