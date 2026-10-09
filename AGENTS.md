# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management.
Supabase Auth, 11 business modules, plain-SQL migrations. Python `>=3.11,<3.13` (`.python-version` pins 3.11.9). Plus an internal
Streamlit audit dashboard (`audit_dashboard.py` + `dashboard/`) — not part of the API.

## Entry Points

- **Dev**: `python run_api.py` — hot reload. Inserts project root into `PYTHONPATH`; breaking this breaks all imports.
- **Prod**: FastAPI Cloud. Root `main.py` re-exports `app.api.main:app` (built via `create_app()`) as the deploy entrypoint.
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
| Install (locked) | `uv sync` |
| Dev server | `python run_api.py` |
| Prod server | `uvicorn app.api.main:app --host 0.0.0.0 --port 8000` |
| Single test | `pytest tests/test_crm.py::test_student_list -v` |
| Local test DB | `scripts/local_test_db.sh up` (also `reset`/`down`; writes `.env.test.local`) |
| Local gate | `pytest -m "not supabase" -v` |
| Cloud Supabase tests | `TEST_ENV_FILE=.env.test pytest -m supabase -v` (needs `TEST_ADMIN_JWT`) |
| All tests (local) | `pytest tests/ -v` (env file chosen in `config.py`; `.env.test.local` wins under pytest) |
| Coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| DB init | `psql "$DATABASE_URL" -f db/schema.sql` |
| Schema verify | `python scripts/verify_test_db.py` |
| Get test JWT | `TESTING=true TEST_ENV_FILE=.env.test python scripts/get_test_jwt.py` |

## Architecture

`app/` is mid-migration to a target shape recorded in `docs/adr/`. Read the relevant ADR before writing, moving, or reviewing code under `app/modules` or `app/api`. New and migrated code follows the target; legacy code is converted one module per ticket, bottom-up.

### Target shape (ADRs)

| ADR | Rule |
|-----|------|
| [0001](docs/adr/0001-one-unit-of-work-per-use-case.md) | One injected `UnitOfWork` per use case; only the top-level use case commits, before external I/O. Services never call `get_session()`. |
| [0002](docs/adr/0002-horizontal-modules-own-their-api.md) | Each module: `api/ → services/ → repositories/ → schemas/, models/`; `__init__.py` is its facade. `app/api/` holds only shared HTTP code. |
| [0003](docs/adr/0003-module-dependency-order-and-facades.md) | Fixed module order, bottom→top: auth, hr, crm, academics, enrollments, attendance, competitions, finance, tasks, notifications, analytics. Import only lower modules, only via their facade. Enforced by import-linter in pytest. |
| [0004](docs/adr/0004-read-any-model-write-only-your-own.md) | Any repository may read any model; writes only to its own module's tables. Raw SQL only in repositories. |
| [0005](docs/adr/0005-auth-is-the-identity-layer-below-hr.md) | auth is the identity layer at the bottom; hr provisions logins through `auth.provision_login()`. |
| [0006](docs/adr/0006-cross-module-writes-live-in-the-highest-module.md) | A write workflow spanning modules lives in the highest module involved. |
| [0007](docs/adr/0007-per-module-notifier-ports.md) | Modules notify through their own Notifier port, called after commit; services take no `BackgroundTasks`. |
| [0008](docs/adr/0008-interfaces-only-where-two-adapters-exist.md) | A Protocol/ABC exists only where two adapters (a test fake counts) satisfy it. |

Rules that hold in both legacy and target code:
- **Repositories**: pure SQLModel queries, zero business rules. Services hold business logic.
- **DTO naming**: Input `{Operation}{Entity}Input`, Output `{Entity}{Operation}Result`, Read `{Entity}{Qualifier}DTO`.
- **Typed Contracts**: services and repositories return named Pydantic DTOs or ORM models (`model_config = ConfigDict(from_attributes=True)`), never `dict`, `list[dict]` or `tuple`.
- **HTTP schemas stay out of services**: services never import a router's request/response schemas.

### Legacy shape (still present in unmigrated modules)

- Routers in `app/api/routers/`, HTTP schemas in `app/api/schemas/`, all service factories in `app/api/dependencies.py`.
- `academics/group/` and `enrollments/` use "D+" sub-slices (`core/`, `directory/`, `lifecycle/`, …) with unreferenced `interface.py` files.
- Two transaction styles: per-module UoWs over the request `get_db()` session (CRM, Finance, HR) and services opening their own `get_session()` (everything else). One request can therefore span several non-atomic sessions. `get_db()` commits after the response is sent and still commits when a rolled-back exception is swallowed, so always re-raise after rollback.
- `get_notification_service()` opens its own session; notification background tasks open fresh sessions because they run after the request closes.

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

### Lifespan Starts Background Tasks
`app/api/main.py` lifespan starts the tasks scheduler (`app/modules/tasks/scheduler.py`) and the Logfire metrics collector (`app/observability/scheduler.py`). `TestClient(app)` used as a context manager triggers lifespan, so they run during tests too. Scheduled reports have no in-process scheduler: an external cron calls `/internal/reports/*` (`app/api/routers/notifications/internal_scheduler_router.py`), guarded by the `X-Internal-Trigger-Secret` header ↔ `settings.internal_trigger_secret` (an empty secret is always rejected).

### Migrations
Plain SQL files in `db/migrations/`. Duplicate prefix numbers exist (`008`, `020`, `021`, `022`, `026`, `030`, `036`, `051`, `057`) — apply in **chronological order**, not numeric. Cleanup migrations: `042`–`049`. Schema: 18 modular files in `db/schema/` applied via `db/schema.sql`. There is no Alembic: migrations are plain SQL files applied by hand.

### Database Pool (code truth in `app/db/connection.py`)
`pool_size=10, max_overflow=5 (15 total), pool_timeout=30, pool_pre_ping=True, pool_recycle=240s`, `sslmode=prefer`, `statement_timeout=30000`, `expire_on_commit=False`.

### Test Isolation
`db_session` fixture uses `get_session()` context manager — rollback only happens if the test raises. Successful tests simply close without explicit rollback; uncommitted mutations are lost on session close. `seeded_session` fixture (module-scoped) explicitly rolls back on teardown for zero side effects between modules. 30+ test files total.

### Testing DB Policy (environment ladder)
| Tier | Target | Allowed |
|------|--------|---------|
| Dev/unit | Local `postgres:17` container (`techno-test-db`, `127.0.0.1:55432`) | Full fast gate, destructive resets (`scripts/local_test_db.sh reset`), migration dry-runs |
| Staging | Supabase **testing** project (`qugffjtucavdseczbata`) | Forward-only migrations FIRST, full pytest gate, live smoke via `TESTING=true python run_api.py` |
| Prod | `srbppkcvrgioneitktdj` | Migrations only after the staging gate is green |

- `.env.test` serves BOTH pytest and the server (`config.py:106` selects it when running under pytest or `TESTING=true`). Its `DATABASE_URL`, `SUPABASE_URL`, and keys must all point at the SAME project — `get_engine()` logs a warning on mismatch (`app/db/connection.py:_warn_on_project_mismatch`).
- **Local gate (#28):** `scripts/local_test_db.sh up` spins up a throwaway `postgres:17` container (`techno-test-db`, `127.0.0.1:55432`), applies `db/schema.sql`, and writes `.env.test.local` (a copy of `.env.test` with only `DATABASE_URL` swapped). Under pytest, `config.py:select_env_file` prefers an explicit `TEST_ENV_FILE`, then `.env.test.local` if present, else `.env.test`. The gate is `pytest -m "not supabase"` — it never touches Supabase. Resets are localhost/container only.
- **`supabase` marker:** registered in `pyproject.toml`. Tests that need real Supabase auth/API are either auto-marked (any test requesting the `admin_token` fixture, via the `pytest_collection_modifyitems` hook in `tests/conftest.py`) or explicitly decorated `@pytest.mark.supabase`. Run them once per sprint against the cloud testing project with `TEST_ENV_FILE=.env.test pytest -m supabase`, after generating a token: `TESTING=true TEST_ENV_FILE=.env.test python scripts/get_test_jwt.py` (export it as `TEST_ADMIN_JWT`); without it, `admin_token` tests skip.
- NEVER apply `db/schema.sql` or reset scripts to the cloud testing DB (it holds restored data) — resets are localhost/CI-container only.
- Suite rows persist on the cloud testing DB by design; everything is uuid-tagged debris.
- Migration ladder: write migration → apply to testing project → green HR/CI gates there → then prod.

### No CI
`.github/` does not exist, so nothing runs on push. Run the tests yourself, against `localhost` Postgres for anything that writes.

### Dead Code Discipline
Before any refactoring, grep for callers of every method. Delete dead code immediately — never migrate it into a new structure. Zero tolerance for commented-out code, deprecated shims, or superseded subset methods.

## Speckit Pipeline

`constitution → specify → clarify → plan → tasks → implement → analyze`. All feature work validates against `.specify/memory/constitution.md`. Active plans live in `specs/*/plan.md`.

## Deployment

- **Platform**: FastAPI Cloud. Entrypoint: root `main.py`. Dependencies come from `pyproject.toml` (`requirements.txt` is gone).
- **Health**: `/health`, `/kaithhealthcheck`.

## Business Reports

Four finalized report queries (new customers, old customers, waiting students, round cost) live in `specs/archive/035-business-reports-feature/spec.md`. Key schema notes: `group_levels` table tracks rounds, `student_status` is an enum (`active`/`waiting`/`inactive`), soft delete via `deleted_at`/`deleted_by`. Always verify against live schema — docs lag behind (README endpoint/table counts are stale).

**Open:** Existing waiting students have NULL `waiting_since` (the migration `068` trigger only covers new transitions; no backfill). Report 3 falls back to `COALESCE(waiting_since, created_at)`. Part-time instructor cost report not yet scoped.

<!-- SPECKIT START -->
Active spec: `specs/041-fix-scheduled-report-date-range/spec.md`
<!-- SPECKIT END -->
