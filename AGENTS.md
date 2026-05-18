# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management.
Supabase Auth, 10 business modules, ~63 migrations. Python 3.10+.

## Entry Points

- **Dev**: `run_api.py` — hot reload. Inserts project root into `PYTHONPATH`; breaking this breaks all imports.
- **Prod factory**: `app.api.main:app` via `create_app()` — used by gunicorn/railpack.

## Required Env (all mandatory unless service is unused)

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`,
`GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`.

Optional PDF settings (defaults in `app/core/config.py`): `pdf_logo_path`, `pdf_company_name`,
`pdf_company_address`, `pdf_primary_signature`, `receipt_company_name`, `receipt_company_address`,
`receipt_tax_id`, `receipt_signature_label`.

## Architecture: Router → Service → Repository

- **Routers** (`app/api/routers/`): HTTP concerns only. Pydantic validation, `Depends()` injection.
- **Services** (`app/modules/*/services/`): Business logic + transaction boundaries (UnitOfWork).
- **Repositories** (`app/modules/*/repositories/`): Pure SQLModel queries. Zero business rules.
- **Two-Layer Schema Rule**: `app/api/schemas/*` is API-only DTO shapes. Services MUST NOT import from `app.api.schemas.*`.
- **D+ Hybrid Pattern**: dominant-entity modules split into sub-slices (`core/`, `directory/`, `lifecycle/`,
  `analytics/`). `models/` is always horizontal per module, never per-slice. Each slice contains exactly:
  `__init__.py`, `interface.py`, `service.py`, `repository.py`, `schemas.py`.
- **Typed Contracts**: No `-> dict`, `-> list[dict]`, or `-> tuple` in services/repositories.
  Returns must be named Pydantic DTOs or ORM models with `model_config = ConfigDict(from_attributes=True)`.

### All Service Factories (in `app/api/dependencies.py`)

| Pattern | Modules | Factories |
|---------|---------|-----------|
| UoW-based | CRM, Finance, HR, Enrollments | session via `get_db()` → UoW wraps session |
| Stateless | Academics, Attendance, Competitions, Analytics | service creates own `get_session()` internally |

Key factories: `get_student_crud_service`, `get_parent_crud_service`, `get_course_service`,
`get_group_service`, `get_session_service`, `get_enrollment_service`,
`get_receipt_service`, `get_refund_service`, `get_balance_service`,
`get_attendance_service`, `get_competition_service`, `get_team_service`,
`get_employee_crud_service`, `get_academic_analytics_service`,
`get_financial_analytics_service`, `get_bi_analytics_service`,
`get_dashboard_service`, `get_notification_service` (owns its own session).

## 10 Modules

`academics` `analytics` `attendance` `auth` `competitions` `crm`
`enrollments` `finance` `hr` `notifications`

## Key Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | `create_app()` factory, middleware order, router registration, lifespan |
| `app/api/dependencies.py` | All DI factories + auth guards |
| `app/api/exceptions.py` | Domain exception → HTTP status handlers |
| `app/shared/exceptions.py` | Domain exception hierarchy (`AppError` base) |
| `app/db/connection.py` | Thread-safe singleton engine; pool config |
| `app/core/supabase_clients.py` | `get_supabase_anon()` cached; `get_supabase_admin()` not cached |
| `app/core/config.py` | Pydantic settings; loads `.env` |
| `.specify/memory/constitution.md` | Architecture constitution — validates all plans against it |

## Commands

| Task | Command |
|------|---------|
| Install deps | `pip install -e .` |
| Dev server | `python run_api.py` |
| Prod server | `uvicorn app.api.main:app --host 0.0.0.0 --port 8000` |
| Single test | `pytest tests/test_crm.py::test_student_list -v` |
| Single-module tests | `pytest tests/test_competitions.py -v` |
| All tests | `pytest tests/ -v` |
| Coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| DB init | `psql -U postgres -d techno_kids -f db/schema.sql` |
| Get test JWT | `python scripts/get_test_jwt.py` |
| Pool tests | `python test_connection_exhaustion.py --uow` |

> Run `pytest tests/` without `--tb=long` when debugging locally — output is verbose enough.

## Auth Flow

1. `Authorization: Bearer <jwt>` → `get_current_user()` validates via Supabase (`get_supabase_anon()`).
2. Maps to local `User` via `get_user_by_supabase_uid()`.
3. Role read from JWT `app_metadata.role`.
   - `require_admin`: `admin` + `system_admin`.
   - `require_any`: any authenticated active user (same callable as `get_current_user`).

**Test tokens**:
- **Real Supabase JWT** — `admin_token` fixture in `tests/conftest.py`, expires ~1h, regen via `python scripts/get_test_jwt.py`.
- **Mock tokens** — `system_admin_token`, `mock_admin_token` via `tests/utils/jwt_mocks.py` (HS256, `TEST_SECRET`).
- **Auth bypass** — `override_auth` fixture replaces `get_current_user` entirely; use with `mock_admin_headers`.

## Response Envelope

```json
{"success": true,  "data": ..., "message": "..."}
{"success": false, "error": "NotFoundError", "message": "..."}
```

## Exception → HTTP Mapping

`NotFoundError`→404, `ValidationError`→422, `BusinessRuleError`→409,
`ConflictError`→409, `AuthError`→401. Pydantic `RequestValidationError` → 422.

## Gotchas

### Router Registration Order
`group_directory_router` MUST register before `groups_router` — `/{group_id}` would shadow `/enriched`.

### Two DI Patterns Coexist
- **UoW-based** (CRM, Finance, HR, Enrollments): session via `get_db()` Depends. `get_db()` commits on
  normal exit and rollbacks on exception via `get_session()` context manager.
- **Stateless** (Academics, Attendance, Competitions, Analytics): services open their own session via
  `get_session()` each call. No UoW, no FastAPI injection.

### UoW Rollback Constraint
`get_db()` generator COMMITS on normal exit. If `uow.rollback()` is called but the exception is
swallowed, `get_db()` still commits. Always re-raise after rollback, or avoid rollback entirely when
the session is `get_db()`-owned.

### Notification Service Gets Its Own Session
`get_notification_service()` opens an independent session — different from the rest of the request.
Intentional: notifications are background/non-transactional.

### DB Engine Config (actual, not spec)
```
pool_size=10, max_overflow=5 (15 total), pool_timeout=30
pool_pre_ping=True, pool_recycle=240s
sslmode=require, statement_timeout=30000, expire_on_commit=False
TCP keepalives: idle=30s, interval=10s, count=5
```

### Migrations
~63 files in `db/migrations/`. Duplicate prefix numbers exist (`008`, `020`, `021`, `022`,
`026`, `030`, `036`, `051`) — apply in **chronological order**, not numeric.
Cleanup migrations: `042`–`049`.

### Response Envelope
All endpoints use the standard envelope. Field names are `success`, `data`, `message`, `error`.

## Testing

`tests/conftest.py` provides:
- `app` (session-scoped), `client` (function-scoped `TestClient`)
- `admin_headers` (real Supabase), `system_admin_headers` / `mock_admin_headers` (mock HS256)
- `db_session` via `get_session()` (explicit rollback in fixture)
- `override_auth` — fully bypass Supabase in test; combine with mock headers

Test helpers in `tests/utils/db_helpers.py`. `test_connection_exhaustion.py` is a standalone
script testing connection pool abuse (run `python test_connection_exhaustion.py --uow`).

## Speckit

Pipeline: `constitution → specify → clarify → plan → tasks → implement → analyze`.  
Commands registered in `.opencode/command/`. All feature work validates against `.specify/memory/constitution.md`.

**Current active plan**: `specs/010-competition-feature-enhancements/plan.md` — Competition Module Bug Fixes
(8 bugs: B1 payment atomicity, B2 non-existent fields, B3 duplicate student warning,
B4 30-day placement window, B5 TOCTOU race, B6 kwargs whitelist, B7/B8 dead code removal).

## Deployment

- **Platform**: Leapcell (`railpack.json`). Build: `pip install -e .`. Start: `uvicorn app.api.main:app`.
- **Health checks**: `/health`, `/kaithhealthcheck`.
- `gunicorn.conf.py` uses `/tmp` for runtime files (read-only filesystem workaround).
- **Docker**: `docker build -t techno-terminal .`

## No CI / Linter / Formatter

No GitHub Actions, no pre-commit, no ruff/flake8/black. Review code / lint manually before
submitting. No opinionated formatter is enforced.
