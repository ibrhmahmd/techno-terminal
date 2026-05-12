# AGENTS.md — Techno Terminal

## Speckit Feature Workflow

This repo has a [Speckit](https://github.com/mark3labs/speckit) workflow for structured feature development. Pipeline: `constitution → specify → clarify → plan → tasks → implement → analyze`.

| Phase | Command | Output |
|-------|---------|--------|
| 1 | `/speckit.specify <description>` | `specs/NNN-feature/spec.md` |
| 2 | `/speckit.clarify` (optional) | Updated spec with resolved ambiguities |
| 3 | `/speckit.plan` | `plan.md`, `research.md`, `data-model.md` |
| 4 | `/speckit.tasks` | `tasks.md` with dependency-ordered checklist |
| 5 | `/speckit.implement` | Executes tasks in order |
| Validate | `/speckit.analyze` | Cross-artifact consistency report |

**Constitution** at `.specify/memory/constitution.md` — all plans/tasks validate against it. `/speckit.plan` checks constitution gates before proceeding. Violations are CRITICAL.

**Templates** at `.specify/templates/` — customizations live there if you need to adjust generated output.

## Quick Commands

| Task | Command |
|------|---------|
| Run API (dev) | `python run_api.py` |
| Run API (prod) | `gunicorn app.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2` |
| Run all tests | `pytest tests/ -v` |
| Run single test | `pytest tests/test_crm.py::test_student_list -v` |
| Run test with coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| Database init | `psql -U postgres -d techno_kids -f db/schema.sql` |
| Get test JWT | `python scripts/get_test_jwt.py` |

## Environment Setup

```env
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/techno_kids
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=...
GMAIL_SENDER_ADDRESS=...
GMAIL_APP_PASSWORD=...
DAILY_REPORT_HOUR=3       # 3 AM
DAILY_REPORT_MINUTE=30
```

## Architecture

### Layer Pattern: Router → Service → Repository

- **Routers** (`app/api/routers/`): FastAPI endpoints, Pydantic validation, `Depends()` injection
- **Services** (`app/modules/*/services/`): Business logic, transaction boundaries (UnitOfWork)
- **Repositories** (`app/modules/*/repositories/`): Pure SQL via SQLModel, no business logic

### Key Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | `create_app()` factory, middleware order, router registration, lifespan |
| `app/api/dependencies.py` | DI factories, auth guards — **two patterns coexist** (see Gotchas) |
| `app/db/connection.py` | Thread-safe singleton engine, pool 5+5=10, SSL require, `statement_timeout=30000ms` |
| `app/core/supabase_clients.py` | `get_supabase_anon()` (cached singleton), `get_supabase_admin()` (not cached) |
| `app/shared/exceptions.py` | Domain exception hierarchy → HTTP status mapping |
| `db/schema.sql` | Orchestrator — includes 17 modular files from `db/schema/` |
| `db/migrations/*.sql` | 49 numbered migrations (some duplicate numbers from parallel branches) |

### Schema Files Order (in `db/schema/`)

`00_extensions` → `01_enums` → `02_core` → `03_crm` → `04_academics` → `05_enrollments` → `06_finance` → `07_competitions` → `08_notifications` → `09_history` → `10_supabase` → `20_indexes` → `30_views` → `40_functions` → `50_triggers` → `60_constraints` → `90_seed_data`

### 10 Business Modules

`academics` | `analytics` | `attendance` | `auth` | `competitions` | `crm` | `enrollments` | `finance` | `hr` | `notifications`

### Entry Points

- `run_api.py` — adds project root to `PYTHONPATH` (required, imports depend on this)
- `app.api.main:app` — via `create_app()` factory (for production / test)
- `Dockerfile` / `railpack.json` — both use Gunicorn/Uvicorn on port 8000

## Authentication & Authorization

1. Client sends `Authorization: Bearer <jwt>` header
2. `get_current_user()` validates via Supabase (`get_supabase_anon()`)
3. `get_user_by_supabase_uid()` maps to local `User` with role
4. Role guards: `require_admin` (allows `admin` + `system_admin`), `require_any` (any authed user)
- Mock test JWTs use HS256 with `TEST_SECRET` at `tests/utils/jwt_mocks.py` — payload puts role in `app_metadata.role`
- Real test JWT comes from `scripts/get_test_jwt.py`, expires ~1 hour

## Testing

### Fixtures (`tests/conftest.py`)

- `app` — session-scoped app via `create_app()`
- `client` — function-scoped `TestClient`
- `admin_token` / `admin_headers` — real Supabase JWT (~1hr expiry)
- `system_admin_token` / `system_admin_headers` — mock JWT from `tests/utils/jwt_mocks.py`
- `db_session` — raw session via `get_session()`, auto-rollback on exception

### Token Regeneration

```bash
python scripts/get_test_jwt.py
# Update `admin_token` in tests/conftest.py
```

## Gotchas

### Router Registration Order

`group_directory_router` **MUST** come before `groups_router` — otherwise `/{group_id}` shadows `/enriched`:

```python
app.include_router(group_directory_router, prefix="/api/v1")  # first
app.include_router(groups_router, prefix="/api/v1")           # second
```

### Two DI Patterns Coexist

1. **UoW-based** (CRM, Finance, HR, Enrollments): `session` injected via `get_db()` Depends → wrapped in UoW → service returned. The session lifecycle (open/commit/close) is managed by FastAPI's `get_db()` generator, NOT the UoW (UoW only owns session when used standalone via `with`).
2. **Stateless** (Academics, Attendance, Competitions, Analytics): services create their own internal sessions.

### UoW Session Gotcha

`get_db()` calls `session.commit()` on normal exit. If a service calls `uow.rollback()` + does NOT re-raise, `get_db()` will still `commit()` afterward. This can commit data after a rollback. Service code must let exceptions propagate, or avoid explicit rollback when using the `get_db()` injection path.

### Notification Service Opens Its Own Session

`get_notification_service()` uses `get_session()` independently — it gets a DIFFERENT database session from the rest of the request. This is intentional (background/non-transactional notifications) but can cause confusion.

### DB Engine Config

- Pool: `pool_size=5`, `max_overflow=5` (10 max), `pool_timeout=30`
- Health: `pool_pre_ping=True`, `pool_recycle=240` (4 min)
- SSL: `sslmode=require`
- Timeout: `statement_timeout=30000` (30s global)
- `expire_on_commit=False` on session

### Response Envelope

```json
{"success": true, "data": ..., "message": "..."}
{"success": false, "error": "NotFoundError", "message": "..."}
```

### Domain Exceptions → HTTP Status

| Exception | Status |
|-----------|--------|
| `NotFoundError` | 404 |
| `ValidationError` | 422 |
| `BusinessRuleError` | 409 |
| `ConflictError` | 409 |
| `AuthError` | 401 |

### Middleware Order (outermost → innermost)

1. Logging middleware
2. CORS middleware (open `*` for dev)
3. Global exception handlers
4. Routers

### Migrations

49 numbered files in `db/migrations/`. Some numbers have duplicates (e.g., `008`, `020`, `021`, `022`, `026`, `030`, `036`) from parallel branches — apply in chronological order, not strictly numeric. Cleanup migrations exist: `042_drop_broken_views.sql` through `049_remove_receipt_tracking_columns.sql`.

## API Documentation

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Deployment

- Platform: Leapcell (configured via `railpack.json`)
- Docker: Gunicorn + Uvicorn, hardcoded port 8000
- Gunicorn config (`gunicorn.conf.py`) uses `/tmp` for runtime files (read-only filesystem fix)
- Health checks at `/health` and `/kaithhealthcheck`
