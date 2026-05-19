# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management.
Supabase Auth, 11 business modules, 62 migrations. Python 3.10+.

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
- **Interface Design**: `@runtime_checkable` Protocol classes named `{Entity}{Concern}Interface` (never `I`-prefix, never `Protocol` suffix). Every public service method must appear in the interface.
- **Import Dependency Chain** (prevents circular imports): `interface.py` → imports from `schemas.py`, `models/` — `schemas.py` → imports from `models/`, shared constants — `repository.py` → imports from `models/`, constants, shared — `service.py` → imports from `repository.py`, `schemas.py`, `interface.py`, helpers. Services MUST NOT import other services within the same module.
- **Cross-Slice Rule**: Repositories CAN be imported across slices (stateless query functions). Services MUST NOT import other services — cross-slice orchestration goes through module root `__init__.py`.
- **DTO Naming**: Input: `{Operation}{Entity}Input` — Output: `{Entity}{Operation}Result` — Read models: `{Entity}{Qualifier}DTO`.
- **Typed Contracts**: No `-> dict`, `-> list[dict]`, or `-> tuple` in services/repositories.
  Returns must be named Pydantic DTOs or ORM models with `model_config = ConfigDict(from_attributes=True)`.

### All Service Factories (in `app/api/dependencies.py`)

| Pattern | Modules | Factories |
|---------|---------|-----------|
| UoW-based | CRM, Finance, HR, Enrollments | session via `get_db()` → UoW wraps session |
| Stateless | Academics, Attendance, Competitions, Analytics | service creates own `get_session()` internally |

Key factories: `get_student_crud_service`, `get_student_search_service`, `get_student_profile_service`,
`get_student_activity_service`, `get_parent_crud_service`, `get_course_service`,
`get_group_service`, `get_group_directory_service`, `get_group_level_service`,
`get_group_analytics_service`, `get_session_service`, `get_enrollment_service`,
`get_enrollment_migration_service`,
`get_receipt_service`, `get_refund_service`, `get_balance_service`, `get_reporting_service`,
`get_student_payment_service`,
`get_attendance_service`, `get_competition_service`, `get_team_service`,
`get_employee_crud_service`, `get_staff_account_service`,
`get_academic_analytics_service`, `get_financial_analytics_service`, `get_bi_analytics_service`,
`get_competition_analytics_service`,
`get_dashboard_service`, `get_notification_service` (owns its own session),
`get_auth_service`.

## 11 Modules

`academics` `analytics` `attendance` `auth` `competitions` `crm`
`enrollments` `finance` `hr` `notifications` `shared`

## Notifications Module (`app/modules/notifications/`)

### Architecture (Facade + Specialized Services)

A `NotificationService` facade delegates to three specialized `BaseNotificationService` subclasses:
```
NotificationService
  ├── .enrollment → EnrollmentNotificationService
  ├── .payment    → PaymentNotificationService
  └── .report     → ReportNotificationService
```

New callers SHOULD use `svc.enrollment.notify_*()` / `svc.payment.notify_*()` / `svc.report.*()` directly. Legacy methods on `NotificationService` are deprecated delegation shims.

### File Layout
```
notifications/
├── models/
│   ├── notification_template.py   # Template with {{variable}} placeholders, is_standard flag
│   └── notification_log.py        # Audit log per dispatch (PENDING→SENT/FAILED)
├── dispatchers/
│   ├── i_dispatcher.py            # IMessageDispatcher Protocol (runtime_checkable)
│   ├── email_dispatcher.py        # Gmail SMTP (smtplib, GMAIL_APP_PASSWORD)
│   └── whatsapp_dispatcher.py     # Twilio (disabled in _dispatch — logs as success)
├── interfaces/
│   └── i_notification_repository.py  # INotificationRepository Protocol
├── repositories/
│   ├── notification_repository.py     # Template + log CRUD
│   └── admin_settings_repository.py   # Per-admin toggles + additional recipients
├── schemas/
│   ├── notification_dto.py, template_dto.py, admin_settings_dto.py
│   ├── send_request.py, fallback_dto.py
├── services/
│   ├── base_notification_service.py    # Shared: _resolve_contact, _dispatch, _resolve_notification_recipients
│   ├── notification_service.py         # Facade with deprecated backward compat methods
│   ├── enrollment_notifications.py     # Enrollment lifecycle notifications (email-only)
│   ├── payment_notifications.py        # Payment + receipt with PDF attachment
│   ├── competition_notifications.py    # Team registration, fee payment, placement
│   ├── report_notifications.py         # Daily/weekly/monthly aggregates + dispatch
│   └── report_scheduler.py            # asyncio polling loop (60s), started at lifespan
├── pdf/
│   └── daily_report_pdf.py            # ReportLab A4 PDF for daily reports
```

### Notification Dispatch Flow

1. `notify_*()` → enqueues via `BackgroundTasks.add_task()` (non-blocking)
2. Background runs `_process_*()` async method
3. `_resolve_notification_recipients()` → reads `notification_additional_recipients` table by notification_type
4. Falls back to `FALLBACK_EMAIL` env var if no valid recipients
5. `_dispatch()` → renders `{{variable}}` placeholders, creates `NotificationLog` (PENDING), sends via `GmailEmailDispatcher`, updates log to SENT/FAILED
6. WhatsApp is **always disabled** — `_dispatch` logs AS success without calling Twilio

### Recipient Resolution (Important)

- All notifications go through `notification_additional_recipients` table
- `AdminSettingsRepository.get_enabled_admins_for_notification()` returns `[]` — intentionally unused
- Fallback: `FALLBACK_EMAIL` env var (default `ibrahim.ahmd.net@gmail.com`)
- Fallback alert: sends an alert email + creates a `FALLBACK_ALERT` notification log entry
- `_resolve_notification_recipients()` also checks email validity via regex

### Reports Features (Daily / Weekly / Monthly)

**`ReportNotificationService`** (`report_notifications.py`):
- `send_daily_report()` / `send_weekly_report()` / `send_monthly_report()`
- Each fetches aggregates, resolves recipients, renders template, dispatches via EMAIL
- Daily report generates a **PDF attachment** via `daily_report_pdf.py` (ReportLab, A4, B&W theme)
- Aggregates fetched via `FinancialAnalyticsService.get_revenue_by_date()` + raw SQL queries for sessions, attendance, payments, enrollment stats
- **TODO**: `_fetch_*_aggregates()` methods return bare `dict` — should be typed DTOs

**`ReportScheduler`** (`report_scheduler.py`):
- Async polling loop started in `create_app()` lifespan
- Checks every 60s if a report window is open (configurable via `DAILY_REPORT_HOUR`/`DAILY_REPORT_MINUTE` env vars, default 20:00)
- Daily: sends when within 5-min window of configured time
- Weekly: also sends on Monday (same window)
- Monthly: also sends on day 1 of month (same window)
- `last_sent` guards prevent double-sends, but **in-memory only** — restart resets them
- Creates its own `NotificationService` (separate session) via factory closure
- **No `SCHEDULER_ENABLED` kill-switch exists yet** — see `012-scheduled-report-audit` spec

**Known Issues (from spec `012-scheduled-report-audit`)**:
- Monthly report covers month-to-date, not preceding full month (needs business clarification)
- Weekly report week-boundary policy unspecified (Sunday vs Monday start)
- No HTTP trigger for manual report dispatch
- In-memory `last_sent` guards are lost on restart (no persistence)
- `_fetch_*_aggregates()` returns `dict` instead of typed DTOs

### Admin Settings API

- Base path: `/api/v1/notifications/admin/settings/me`
- 13 notification types managed via `admin_notification_settings` table
- Additional recipients CRUD at `/settings/me/additional-recipients/`
- Global (shared) settings — `SYSTEM_ADMIN_ID = 1`, not per-admin
- Template CRUD + test at `/api/v1/templates/{id}/test` (actually sends test email)

### Notification Templates (13 standard templates)

| Template Name | Channel | Purpose |
|--------------|---------|---------|
| `daily_report` | EMAIL | Daily business summary + PDF |
| `weekly_report` | EMAIL | Weekly revenue + new students |
| `monthly_report` | EMAIL | Monthly revenue + enrollments |
| `enrollment_*` (5) | EMAIL | Created, completed, dropped, transferred, level progression |
| `payment_*` (2) | EMAIL | Receipt + reminder |
| `competition_*` (3) | EMAIL | Team registration, fee payment, placement |

Standard templates (`is_standard=True`) cannot be deleted; name/channel/variables protected from update.

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
62 files in `db/migrations/`. Duplicate prefix numbers exist (`008`, `020`, `021`, `022`,
`026`, `030`, `036`, `051`) — apply in **chronological order**, not numeric.
Cleanup migrations: `042`–`049`.
Schema: 17 modular files in `db/schema/` applied in dependency order via `db/schema.sql`.

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

**Recent specs**: `011-session-level-integrity` (session-group level FK integrity),
`012-scheduled-report-audit` (scheduled report generation audit).

## Deployment

- **Platform**: Leapcell (`railpack.json`). Build: `pip install -e .`. Start: `uvicorn app.api.main:app`.
- **Health checks**: `/health`, `/kaithhealthcheck`.
- `gunicorn.conf.py` uses `/tmp` for runtime files (read-only filesystem workaround).
- **Docker**: `docker build -t techno-terminal .`

## No CI / Linter / Formatter

No GitHub Actions, no pre-commit, no ruff/flake8/black. Review code / lint manually before
submitting. No opinionated formatter is enforced.

## Dead Code Discipline

Before any refactoring or migration, grep for callers of every method. Delete dead code
immediately — never migrate it into a new structure. Zero tolerance for commented-out code,
deprecated methods kept for "backward compatibility," or subset methods superseded by broader
equivalents.
