# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management. Supabase Auth, 10 business modules, 56 migrations.

## Entry Points

- `run_api.py` — dev (hot reload). Adds project root to `PYTHONPATH` (required, imports depend on this).
- `app.api.main:app` — `create_app()` factory, used by gunicorn/railpack in production.

## Quick Commands

| Task | Command |
|------|---------|
| Run API (dev) | `python run_api.py` |
| Run API (prod) | `gunicorn app.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2` |
| Run all tests | `pytest tests/ -v` |
| Single test | `pytest tests/test_crm.py::test_student_list -v` |
| Coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| DB init | `psql -U postgres -d techno_kids -f db/schema.sql` |
| Get test JWT | `python scripts/get_test_jwt.py` |

## Speckit Feature Workflow

Pipeline: `constitution → specify → clarify → plan → tasks → implement → analyze`. Commands: `/speckit.specify <desc>`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.analyze`. Constitution at `.specify/memory/constitution.md` — all plans/tasks validate against it.

## Required Env

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, `GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`.

## Architecture

### Layer Pattern: Router → Service → Repository

- **Routers** (`app/api/routers/`): FastAPI endpoints, Pydantic, `Depends()` injection
- **Services** (`app/modules/*/services/`): Business logic, transaction boundaries (UnitOfWork)
- **Repositories** (`app/modules/*/repositories/`): Pure SQL via SQLModel, no business logic

### 10 Modules

`academics` | `analytics` | `attendance` | `auth` | `competitions` | `crm` | `enrollments` | `finance` | `hr` | `notifications`

### Schema Order (`db/schema/`)

`00_extensions` → `01_enums` → `02_core` → `03_crm` → `04_academics` → `05_enrollments` → `06_finance` → `07_competitions` → `08_notifications` → `09_history` → `10_supabase` → `20_indexes` → `30_views` → `40_functions` → `50_triggers` → `60_constraints` → `90_seed_data`

### Key Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | `create_app()` factory, middleware order, router registration, lifespan |
| `app/api/dependencies.py` | DI factories, auth guards — **two patterns coexist** (see Gotchas) |
| `app/db/connection.py` | Thread-safe singleton engine, pool 5+5=10, SSL require, 30s timeout |
| `app/core/supabase_clients.py` | `get_supabase_anon()` (cached), `get_supabase_admin()` (not cached) |
| `app/shared/exceptions.py` | Domain exception hierarchy → HTTP status mapping |
| `db/schema.sql` | Orchestrator — includes 17 modular files |
| `db/migrations/*.sql` | 56 numbered files (some duplicates from parallel branches) |

## Auth

1. `Authorization: Bearer <jwt>` → `get_current_user()` validates via Supabase (`get_supabase_anon()`)
2. Maps to local `User` with role via `get_user_by_supabase_uid()`
3. Role from JWT `app_metadata.role`; guards: `require_admin` (`admin` + `system_admin`), `require_any`
- **Mock test JWTs** (HS256, `TEST_SECRET` in `tests/utils/jwt_mocks.py`) — place role in `app_metadata.role`
- **Real test JWT** from `python scripts/get_test_jwt.py`, expires ~1hr, update `admin_token` in `tests/conftest.py`

## Testing Fixtures (`tests/conftest.py`)

- `app` (session-scoped), `client` (function-scoped `TestClient`)
- `admin_token`/`admin_headers` (real Supabase JWT), `system_admin_token`/`system_admin_headers` (mock JWT)
- `db_session` via `get_session()`, auto-rollback on exception
- Test data helpers in `tests/utils/db_helpers.py`

## Gotchas

### Router Registration Order
`group_directory_router` **MUST** come before `groups_router` — `/{group_id}` shadows `/enriched` otherwise.

### Two DI Patterns Coexist
1. **UoW-based** (CRM, Finance, HR, Enrollments): session via `get_db()` Depends → wrapped in UoW. Session lifecycle managed by FastAPI `get_db()` generator, NOT the UoW.
2. **Stateless** (Academics, Attendance, Competitions, Analytics): services create their own internal sessions.

### UoW Rollback Constraint
`get_db()` calls `session.commit()` on normal exit. If a service calls `uow.rollback()` without re-raising, `get_db()` will still `commit()`. Let exceptions propagate after rollback.

### Notification Service Opens Its Own Session
`get_notification_service()` uses `get_session()` independently — gets a DIFFERENT DB session from the rest of the request (intentional for background notifications).

### DB Engine Config
Pool: 5+5=10, `pool_pre_ping=True`, `pool_recycle=240s`, `sslmode=require`, `statement_timeout=30000`, `expire_on_commit=False`.

### Response Envelope
```json
{"success": true, "data": ..., "message": "..."}
{"success": false, "error": "NotFoundError", "message": "..."}
```

### Domain Exceptions → HTTP
`NotFoundError`→404, `ValidationError`→422, `BusinessRuleError`→409, `ConflictError`→409, `AuthError`→401

### Middleware Order (outer→inner)
1. Logging → 2. CORS (`*` for dev) → 3. Exception handlers → 4. Routers

### Migrations
56 files in `db/migrations/`. Duplicate numbers exist (`008`, `020`, `021`, `022`, `026`, `030`, `036`). Apply in chronological order, not strictly numeric. Cleanup migrations: `042`–`049`.

## Deployment
- Platform: Leapcell (`railpack.json`)
- Health checks at `/health` and `/kaithhealthcheck`
- `gunicorn.conf.py` uses `/tmp` for runtime files (read-only filesystem fix)

## Connection Pool Tests
Standalone suite at `test_connection_exhaustion.py` — tests UoW pattern abuse, scheduler leaks, stale connections, slow queries. Run with `python test_connection_exhaustion.py --uow` (10s) or `--all-direct`.

<!-- SPECKIT START -->
**Current Plan**: `specs/007-review-competition-routers/plan.md` — Review Competition Routers
<!-- SPECKIT END -->
