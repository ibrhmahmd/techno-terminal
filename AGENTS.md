# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management.
Supabase Auth, 10 business modules, 68 migrations. Python 3.10+.

## Entry Points

- **Dev**: `python run_api.py` — hot reload. Inserts project root into `PYTHONPATH`; breaking this breaks all imports.
- **Prod**: `uvicorn app.api.main:app` (via `create_app()`) — used by gunicorn/railpack.

## Required Env

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`,
`GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`.

Optional PDF/receipt settings in `app/core/config.py` (env-driven).

## Commands

| Task | Command |
|------|---------|
| Install deps | `pip install -e .` |
| Dev server | `python run_api.py` |
| Prod server | `uvicorn app.api.main:app --host 0.0.0.0 --port 8000` |
| Single test | `pytest tests/test_crm.py::test_student_list -v` |
| All tests | `pytest tests/ -v` |
| Coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| DB init | `psql "$DATABASE_URL" -f db/schema.sql` |
| Get test JWT | `python scripts/get_test_jwt.py` |
| Pool tests | `python test_connection_exhaustion.py --uow` |

> Run `pytest tests/` without `--tb=long` for local debugging.

## Architecture: Router → Service → Repository

- **Routers** (`app/api/routers/`): HTTP only — Pydantic validation, `Depends()` injection.
- **Services** (`app/modules/*/services/`): Business logic + transaction boundaries.
- **Repositories** (`app/modules/*/repositories/`): Pure SQLModel queries. Zero business rules.
- **Two-Layer Schema Rule**: `app/api/schemas/*` is API-only DTOs. Services MUST NOT import from `app.api.schemas.*`.
- **DTO naming**: Input `{Operation}{Entity}Input`, Output `{Entity}{Operation}Result`, Read `{Entity}{Qualifier}DTO`.
- **Typed Contracts**: No `-> dict`, `-> list[dict]`, `-> tuple` in services/repositories. Return named Pydantic DTOs or ORM models with `model_config = ConfigDict(from_attributes=True)`.

### D+ Hybrid Pattern (dominant-entity modules)

`academics/group/` and `enrollments/` split into sub-slices (`core/`, `directory/`, `lifecycle/`, `analytics/`). Models stay horizontal (`models/` per module, never per-slice). Each slice contains: `__init__.py`, `interface.py`, `service.py`, `repository.py`, `schemas.py`. CRM uses traditional horizontal layers (`services/`, `repositories/`, `models/`, `schemas/`) — not D+.

**Interface design**: `@runtime_checkable` Protocols named `{Entity}{Concern}Interface` (no `I-` prefix, no `Protocol` suffix). Every public service method appears in the interface.

**Import chain** (prevents circulars): `interface.py` → `schemas.py`, `models/` → `repository.py` → `service.py`. Services MUST NOT import other services within the same module. Cross-slice orchestration goes through module root `__init__.py`. Repositories CAN cross slices.

### All Service Factories (in `app/api/dependencies.py`)

| Pattern | Modules | Mechanism |
|---------|---------|-----------|
| UoW-based | CRM, Finance, HR, Enrollments | session via `get_db()` Depends → UoW wraps session |
| Stateless | Academics, Attendance, Competitions, Analytics | service opens `get_session()` internally |

Key factories: `get_student_crud_service`, `get_student_search_service`, `get_student_profile_service`,
`get_student_activity_service`, `get_parent_crud_service`, `get_course_service`,
`get_group_service`, `get_group_directory_service`, `get_group_level_service`,
`get_group_analytics_service`, `get_session_service`, `get_enrollment_service`,
`get_enrollment_migration_service`, `get_receipt_service`, `get_refund_service`, `get_balance_service`,
`get_reporting_service`, `get_student_payment_service`, `get_attendance_service`,
`get_competition_service`, `get_team_service`, `get_employee_crud_service`, `get_staff_account_service`,
`get_academic_analytics_service`, `get_financial_analytics_service`, `get_bi_analytics_service`,
`get_competition_analytics_service`, `get_dashboard_service`, `get_notification_service` (own session),
`get_auth_service`.

## Modules

`academics` `analytics` `attendance` `auth` `competitions` `crm` `enrollments` `finance` `hr` `notifications`

Cross-cutting utilities in `app/shared/` (exceptions, validators, base_repository, constants).

## Auth Flow

1. `Authorization: Bearer <jwt>` → `get_current_user()` validates via Supabase (`get_supabase_anon()`).
2. Maps to local `User` via `get_user_by_supabase_uid()`.
3. Role from JWT `app_metadata.role`. `require_admin`: `admin` + `system_admin`. `require_any`: any authenticated active user.

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

## Notifications Module

**Architecture**: `NotificationService` facade → 3 specialized `BaseNotificationService` subclasses (`.enrollment`, `.payment`, `.report`). Background dispatch via `BackgroundTasks.add_task()`.

**Dispatch flow**: `notify_*()` → enqueues → `_resolve_notification_recipients()` → reads `notification_additional_recipients` table → falls back to `FALLBACK_EMAIL` (default `ibrahim.ahmd.net@gmail.com`) → `_dispatch()` renders `{{variable}}` placeholders, creates `NotificationLog` (PENDING), sends via Gmail SMTP, updates to SENT/FAILED. WhatsApp always logs as success without calling Twilio.

**ReportScheduler**: asyncio polling loop (60s) started at app lifespan. Checks `settings.scheduler_enabled` (env `SCHEDULER_ENABLED`, default true). Daily at configurable hour/minute (default 20:00, 5-min window). Weekly also on Monday, monthly also on day 1. `last_sent` guards are in-memory only — restart resets them.

**PDF**: Daily report generates ReportLab A4 PDF attachment via `daily_report_pdf.py`.

## Gotchas

### Router Registration Order
`group_directory_router` MUST register before `groups_router` — `/{group_id}` shadows `/enriched`.

### Two DI Patterns
- **UoW-based** (CRM, Finance, HR, Enrollments): `get_db()` commits on normal exit, rollbacks on exception. If `uow.rollback()` is called but the exception is swallowed, `get_db()` still commits. Always re-raise after rollback.
- **Stateless** (Academics, Attendance, Competitions, Analytics): services open their own `get_session()` per call.

### Notification Service Gets Its Own Session
`get_notification_service()` opens an independent session (different from the rest of the request). Intentional: background/non-transactional.

### Database Pool (code truth)
`pool_size=10, max_overflow=5 (15 total), pool_timeout=30, pool_pre_ping=True, pool_recycle=240s`, `sslmode=require`, `statement_timeout=30000`, `expire_on_commit=False`.

### Migrations
68 files in `db/migrations/`. Duplicate prefix numbers exist (`008`, `020`, `021`, `022`, `026`, `030`, `036`, `051`) — apply in **chronological order**, not numeric. Cleanup migrations: `042`–`049`. Schema: 17 modular files in `db/schema/` applied via `db/schema.sql`. `alembic/` directory and `alembic.ini` do NOT exist (Dockerfile reference is stale).

### Test Isolation
`db_session` fixture uses `get_session()` context manager — rollback only happens if the test raises. Successful tests simply close without explicit rollback; uncommitted mutations are lost on session close.

### No CI / Linter / Formatter
No GitHub Actions, pre-commit, ruff, flake8, or black. Review/lint manually.

### Dead Code Discipline
Before any refactoring, grep for callers of every method. Delete dead code immediately — never migrate it into a new structure. Zero tolerance for commented-out code, deprecated shims kept for "backward compat", or superseded subset methods.

## Speckit Pipeline

`constitution → specify → clarify → plan → tasks → implement → analyze`
Commands in `.opencode/command/`. All feature work validates against `.specify/memory/constitution.md`.

## Deployment

- **Platform**: Leapcell (`railpack.json`). Build: `pip install -e .`. Start: `uvicorn app.api.main:app`.
- **Health**: `/health`, `/kaithhealthcheck`.
- `gunicorn.conf.py` uses `/tmp` for runtime files (read-only filesystem workaround).
- **Docker**: `docker build -t techno-terminal .` (note: references missing `alembic/` directory).

<!-- SPECKIT START -->
Active plan: `specs/023-system-contract/plan.md`
<!-- SPECKIT END -->
