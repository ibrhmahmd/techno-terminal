# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management. Supabase Auth, 10 business modules, 62 migrations. Python 3.10+.

## Entry Points

- `run_api.py` — dev (hot reload). Adds project root to `PYTHONPATH` (required, imports depend on this).
- `app.api.main:app` — `create_app()` factory, used by gunicorn/railpack in production.

## Quick Commands

| Task | Command |
|------|---------|
| Install deps | `pip install -e .` |
| Run API (dev) | `python run_api.py` |
| Run API (prod) | `gunicorn app.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2` |
| Run all tests | `pytest tests/ -v` |
| Single test | `pytest tests/test_crm.py::test_student_list -v` |
| Coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| DB init | `psql -U postgres -d techno_kids -f db/schema.sql` |
| Get test JWT | `python scripts/get_test_jwt.py` |
| Pool exhaustion tests | `python test_connection_exhaustion.py --uow` |

## Required Env

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, `GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`.

## Architecture: Router → Service → Repository

- **Routers** (`app/api/routers/`): FastAPI endpoints, Pydantic, `Depends()` injection
- **Services** (`app/modules/*/services/`): Business logic, transaction boundaries (UnitOfWork)
- **Repositories** (`app/modules/*/repositories/`): Pure SQL via SQLModel, no business logic
- **Two-Layer Schema Rule**: `app/api/schemas/` only for API-specific DTO shapes. Services MUST NOT import from `app.api.schemas.*`. DTOs that model domain concepts live beside their service.
- **D+ Hybrid Pattern**: Modules with a dominant entity and ≥3 workflow concerns use sub-slices (`core/`, `directory/`, `lifecycle/`, `analytics/`). `models/` is always horizontal (shared per module), never per-slice.
- **Typed Contracts**: Service methods MUST NOT return bare `dict`, `list[dict]`, or `tuple`. All returns must be typed Pydantic DTOs or ORM models with `model_config = ConfigDict(from_attributes=True)`.
- **Dead Code Discipline**: Before refactoring, grep for callers of every method. Delete dead code immediately — never migrate it. Zero tolerance for commented-out code or superseded methods.

### 10 Modules

`academics` | `analytics` | `attendance` | `auth` | `competitions` | `crm` | `enrollments` | `finance` | `hr` | `notifications`

### Key Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | `create_app()` factory, middleware order, router registration, lifespan (report scheduler) |
| `app/api/dependencies.py` | DI factories, auth guards — **two patterns coexist** (see Gotchas) |
| `app/api/exceptions.py` | Domain exception → HTTP status handlers |
| `app/shared/exceptions.py` | Domain exception hierarchy (`AppError` base) |
| `app/db/connection.py` | Thread-safe singleton engine, pool 10+5=15, SSL require, 30s timeout |
| `app/core/supabase_clients.py` | `get_supabase_anon()` (cached), `get_supabase_admin()` (not cached, requires SERVICE_ROLE_KEY) |
| `.specify/memory/constitution.md` | Architecture constitution — all feature work validates against it |

## Auth

1. `Authorization: Bearer <jwt>` → `get_current_user()` validates via Supabase (`get_supabase_anon()`)
2. Maps to local `User` with role via `get_user_by_supabase_uid()`
3. Role from JWT `app_metadata.role`; guards: `require_admin` (`admin` + `system_admin`), `require_any`
- **Mock test JWTs** (HS256, `TEST_SECRET` in `tests/utils/jwt_mocks.py`) — place role in `app_metadata.role`
- **Real test JWT** from `python scripts/get_test_jwt.py`, expires ~1hr, update `admin_token` in `tests/conftest.py`

## Testing Fixtures (`tests/conftest.py`)

- `app` (session-scoped), `client` (function-scoped `TestClient`)
- `admin_headers` (real Supabase JWT), `system_admin_headers` (mock JWT), `mock_admin_headers` (mock JWT)
- `db_session` via `get_session()`, auto-rollback on exception
- `override_auth` fixture to bypass Supabase validation entirely
- Test data helpers in `tests/utils/db_helpers.py`
- 23 test modules

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
Pool: 10+5=15 max, `pool_pre_ping=True`, `pool_recycle=240s`, `sslmode=require`, `statement_timeout=30000`, `expire_on_commit=False`, TCP keepalives enabled.

### Response Envelope
```json
{"success": true, "data": ..., "message": "..."}
{"success": false, "error": "NotFoundError", "message": "..."}
```

### Domain Exceptions → HTTP
`NotFoundError`→404, `ValidationError`→422, `BusinessRuleError`→409, `ConflictError`→409, `AuthError`→401. `RequestValidationError` (Pydantic) also → 422.

### Middleware Order (outer→inner)
Logging → CORS (`*` for dev) → Exception handlers → Routers

### Migrations
62 files in `db/migrations/`. Duplicate numbers exist (`008`, `020`, `021`, `022`, `026`, `030`, `036`). Apply in chronological order, not strictly numeric. Cleanup migrations: `042`–`049`.

### No CI / Linter / Formatter
No GitHub Actions, no pre-commit, no ruff/flake8/black config. Review code manually.

## Deployment
- Platform: Leapcell (`railpack.json`) — build: `pip install -e .`, start: `uvicorn app.api.main:app`
- Health checks at `/health` and `/kaithhealthcheck`
- `gunicorn.conf.py` uses `/tmp` for runtime files (read-only filesystem fix)
- Docker: `docker build -t techno-terminal .`

## Speckit Feature Workflow

Pipeline: `constitution → specify → clarify → plan → tasks → implement → analyze`. Commands: `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.analyze`. All plans/tasks validate against `.specify/memory/constitution.md`.

14 speckit commands registered in `.opencode/command/`.

## Connection Pool Tests
Standalone suite at `test_connection_exhaustion.py` — tests UoW pattern abuse, scheduler leaks, stale connections, slow queries. Run with `python test_connection_exhaustion.py --uow` (10s) or `--all-direct`.

<!-- SPECKIT START -->
**Current Plan**: `specs/010-competition-feature-enhancements/plan.md` — Competition Module Bug Fixes (8 bugs: payment atomicity, non-existent fields, duplicate student warning, 30-day placement window, TOCTOU race, kwargs whitelist, dead code removal)
<!-- SPECKIT END -->
