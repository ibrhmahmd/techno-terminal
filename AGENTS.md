# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management.
Supabase Auth, 11 business modules, 87 migrations. Python 3.10+. Plus an internal
Streamlit audit dashboard (`audit_dashboard.py` + `dashboard/`) — not part of the API.

## Entry Points

- **Dev**: `python run_api.py` — hot reload. Inserts project root into `PYTHONPATH`; breaking this breaks all imports.
- **Prod**: `uvicorn app.api.main:app` (via `create_app()`) — used by gunicorn/railpack.
- **Dashboard**: `streamlit run audit_dashboard.py`.

## Required Env

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`,
`GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`.

Optional PDF/receipt settings in `app/core/config.py`.

## Commands

| Task | Command |
|------|---------|
| Install deps | `pip install -e .` |
| Dev server | `python run_api.py` |
| Prod server | `uvicorn app.api.main:app --host 0.0.0.0 --port 8000` |
| Single test | `pytest tests/test_crm.py::test_student_list -v` |
| All tests (local) | `pytest tests/ -v` (auto-loads `.env.test` via `config.py:106`) |
| Coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| DB init | `psql "$DATABASE_URL" -f db/schema.sql` |
| Schema verify | `python scripts/verify_test_db.py` |
| Get test JWT | `python scripts/get_test_jwt.py` |
| Pool tests | `pytest tests/test_connection_exhaustion.py -v` |

## Architecture: Router → Service → Repository

- **Routers** (`app/api/routers/`): HTTP only — Pydantic validation, `Depends()` injection.
- **Services** (`app/modules/*/services/`): Business logic + transaction boundaries.
- **Repositories** (`app/modules/*/repositories/`): Pure SQLModel queries. Zero business rules.
- **Two-Layer Schema Rule**: `app/api/schemas/*` is API-only DTOs. Services MUST NOT import from `app.api.schemas.*`.
- **DTO naming**: Input `{Operation}{Entity}Input`, Output `{Entity}{Operation}Result`, Read `{Entity}{Qualifier}DTO`.
- **Typed Contracts**: No `-> dict`, `-> list[dict]`, `-> tuple` in services/repositories. Return named Pydantic DTOs or ORM models with `model_config = ConfigDict(from_attributes=True)`.

### D+ Hybrid Pattern (dominant-entity modules)

`academics/group/` and `enrollments/` split into sub-slices (`core/`, `directory/`, `lifecycle/`, plus domain-specific ones). Models stay horizontal (`models/` per module, never per-slice). Each slice contains: `__init__.py`, `interface.py`, `service.py`, `repository.py`, `schemas.py`. CRM uses traditional horizontal layers — not D+.

**Interface design**: `@runtime_checkable` Protocols named `{Entity}{Concern}Interface` (no `I-` prefix, no `Protocol` suffix).

**Import chain**: `interface.py` → `schemas.py`, `models/` → `repository.py` → `service.py`. Services MUST NOT import other services within the same module. Cross-slice orchestration goes through module root `__init__.py`. Repositories CAN cross slices.

### Two DI Patterns

- **UoW-based** (CRM, Finance, HR, Enrollments): `get_db()` yields session, commits on normal exit, rollbacks on exception. If `uow.rollback()` is called but the exception is swallowed, `get_db()` still commits — always re-raise after rollback.
- **Stateless** (Academics, Attendance, Competitions, Analytics): services open their own `get_session()` per call.

All service factories in `app/api/dependencies.py`.

### Notification Service Gets Its Own Session

`get_notification_service()` opens an independent session (different from the rest of the request). Intentional: background/non-transactional.

## Auth Flow

1. `Authorization: Bearer <jwt>` → `get_current_user()` validates via Supabase (`get_supabase_anon()`).
2. Maps to local `User` via `get_user_by_supabase_uid()`.
3. Role comes from the **local `users.role` column** (JWT only proves identity). Role guards in `app/api/dependencies.py:112-118`: `require_admin` (`admin` + `system_admin`), `require_system_admin`, `require_any` (alias for `get_current_user`), plus `require_coach_or_admin` (`dependencies.py:340`).

**Test tokens**:
- **Real Supabase JWT** — `admin_token` fixture in `tests/conftest.py`, expires ~1h, regen via `python scripts/get_test_jwt.py`.
- **Mock tokens** — `system_admin_token`, `mock_admin_token` via `tests/utils/jwt_mocks.py` (HS256, `TEST_SECRET`).
- **Auth bypass** — `override_auth` fixture replaces `get_current_user` entirely; pair with mock headers.

## Response Envelope

```json
{"success": true,  "data": ..., "message": "..."}
{"success": false, "error": "NotFoundError", "message": "..."}
```

## Exception → HTTP Mapping

`NotFoundError`→404, `ValidationError`→422, `BusinessRuleError`→409, `ConflictError`→409, `AuthError`→401. Pydantic `RequestValidationError`→422.

## Gotchas

### Router Registration Order
`group_directory_router` MUST register before `groups_router` — `/{group_id}` shadows `/enriched`. Confirmed in `app/api/main.py:116-120`.

### Lifespan Starts Background Schedulers
`app/api/main.py` lifespan spawns the notifications report scheduler and the tasks scheduler (`asyncio.create_task`). `TestClient(app)` used as a context manager triggers lifespan, so schedulers run during tests too.

### `get_group_analytics_service` defined twice
Defined at `dependencies.py:213` and `dependencies.py:411`. Python uses the last definition (line 411 wins). Same interface.

### Migrations
87 files in `db/migrations/`. Duplicate prefix numbers exist (`008`, `020`, `021`, `022`, `026`, `030`, `036`, `051`, `057`) — apply in **chronological order**, not numeric. Cleanup migrations: `042`–`049`. Schema: 18 modular files in `db/schema/` applied via `db/schema.sql`. `alembic/` directory and `alembic.ini` do NOT exist (but `Dockerfile` references them — stale).

### Database Pool (code truth in `app/db/connection.py`)
`pool_size=10, max_overflow=5 (15 total), pool_timeout=30, pool_pre_ping=True, pool_recycle=240s`, `sslmode=prefer`, `statement_timeout=30000`, `expire_on_commit=False`.

### Test Isolation
`db_session` fixture uses `get_session()` context manager — rollback only happens if the test raises. Successful tests simply close without explicit rollback; uncommitted mutations are lost on session close. `seeded_session` fixture (module-scoped) explicitly rolls back on teardown for zero side effects between modules. 30+ test files total.

### Testing DB Policy (environment ladder)
| Tier | Target | Allowed |
|------|--------|---------|
| Dev/unit | `localhost/techno` | Full fast gate, destructive resets (`db/schema.sql`), migration dry-runs |
| Staging | Supabase **testing** project (`qugffjtucavdseczbata`) | Forward-only migrations FIRST, full pytest gate, live smoke via `TESTING=true python run_api.py` |
| Prod | `srbppkcvrgioneitktdj` | Migrations only after the staging gate is green |

- `.env.test` serves BOTH pytest and the server (`config.py:106` selects it when running under pytest or `TESTING=true`). Its `DATABASE_URL`, `SUPABASE_URL`, and keys must all point at the SAME project — `get_engine()` logs a warning on mismatch (`app/db/connection.py:_warn_on_project_mismatch`).
- NEVER apply `db/schema.sql` or reset scripts to the cloud testing DB (it holds restored data) — resets are localhost/CI-container only.
- Suite rows persist on the cloud testing DB by design; everything is uuid-tagged debris.
- Migration ladder: write migration → apply to testing project → green HR/CI gates there → then prod.

### CI Pipeline
`.github/workflows/ci.yml` runs on every push/PR:
- **Backend only**: Ubuntu, PostgreSQL 15 service, Python 3.10, applies `db/schema.sql` via `cd db && psql`, seeds via `scripts/ci_seed_database.py`, runs **only** `pytest tests/test_finance.py tests/test_crm.py -v` (not the full suite).
- External services (Supabase, Twilio, Gmail) use mock-safe dummy values — no production credentials.
- **No frontend CI** in this workflow (despite what README claims).

### Dead Code Discipline
Before any refactoring, grep for callers of every method. Delete dead code immediately — never migrate it into a new structure. Zero tolerance for commented-out code, deprecated shims, or superseded subset methods.

## Speckit Pipeline

`constitution → specify → clarify → plan → tasks → implement → analyze`. All feature work validates against `.specify/memory/constitution.md`. Active plans live in `specs/*/plan.md`.

## Deployment

- **Platform**: Leapcell (`railpack.json`). Build: `pip install -e .`. Start: `uvicorn app.api.main:app`.
- `gunicorn.conf.py` uses `/tmp` for runtime files (read-only filesystem workaround).
- **Health**: `/health`, `/kaithhealthcheck`.

## Business Reports

Four finalized report queries (new customers, old customers, waiting students, round cost) live in `specs/035-business-reports-feature/spec.md`. Key schema notes: `group_levels` table tracks rounds, `student_status` is an enum (`active`/`waiting`/`inactive`), soft delete via `deleted_at`/`deleted_by`. Always verify against live schema — docs lag behind (README endpoint/table counts are stale).

**Open:** Existing waiting students have NULL `waiting_since` (the migration `068` trigger only covers new transitions; no backfill). Report 3 falls back to `COALESCE(waiting_since, created_at)`. Part-time instructor cost report not yet scoped.

<!-- SPECKIT START -->
Active plan: `specs/040-employee-soft-delete/plan.md`
<!-- SPECKIT END -->
