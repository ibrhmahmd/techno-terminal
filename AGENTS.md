# AGENTS.md — Techno Terminal

FastAPI + SQLModel + PostgreSQL backend for STEM education center management.
Supabase Auth, 11 business modules, 83 migrations. Python 3.10+.

## Entry Points

- **Dev**: `python run_api.py` — hot reload. Inserts project root into `PYTHONPATH`; breaking this breaks all imports.
- **Prod**: `uvicorn app.api.main:app` (via `create_app()`) — used by gunicorn/railpack.

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
| Pool tests | `python test_connection_exhaustion.py --uow` |

## Architecture: Router → Service → Repository

- **Routers** (`app/api/routers/`): HTTP only — Pydantic validation, `Depends()` injection.
- **Services** (`app/modules/*/services/`): Business logic + transaction boundaries.
- **Repositories** (`app/modules/*/repositories/`): Pure SQLModel queries. Zero business rules.
- **Two-Layer Schema Rule**: `app/api/schemas/*` is API-only DTOs. Services MUST NOT import from `app.api.schemas.*`.
- **DTO naming**: Input `{Operation}{Entity}Input`, Output `{Entity}{Operation}Result`, Read `{Entity}{Qualifier}DTO`.
- **Typed Contracts**: No `-> dict`, `-> list[dict]`, `-> tuple` in services/repositories. Return named Pydantic DTOs or ORM models with `model_config = ConfigDict(from_attributes=True)`.

### D+ Hybrid Pattern (dominant-entity modules)

`academics/group/` and `enrollments/` split into sub-slices (`core/`, `directory/`, `lifecycle/`, `analytics/`). Models stay horizontal (`models/` per module, never per-slice). Each slice contains: `__init__.py`, `interface.py`, `service.py`, `repository.py`, `schemas.py`. CRM uses traditional horizontal layers — not D+.

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
3. Role from JWT `app_metadata.role`. Role guards: `require_admin` (`admin` + `system_admin`), `require_system_admin`, `require_any` (any authenticated active user).

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
`group_directory_router` MUST register before `groups_router` — `/{group_id}` shadows `/enriched`. Confirmed in `app/api/main.py:107-110`.

### `get_group_analytics_service` defined twice
Defined at `dependencies.py:213` and `dependencies.py:411`. Python uses the last definition (line 411 wins). Same interface.

### Migrations
83 files in `db/migrations/`. Duplicate prefix numbers exist (`008`, `020`, `021`, `022`, `026`, `030`, `036`, `051`) — apply in **chronological order**, not numeric. Cleanup migrations: `042`–`049`. Schema: 17 modular files in `db/schema/` applied via `db/schema.sql`. `alembic/` directory and `alembic.ini` do NOT exist (but `Dockerfile` references them — stale).

### Database Pool (code truth in `app/db/connection.py`)
`pool_size=10, max_overflow=5 (15 total), pool_timeout=30, pool_pre_ping=True, pool_recycle=240s`, `sslmode=prefer`, `statement_timeout=30000`, `expire_on_commit=False`.

### Test Isolation
`db_session` fixture uses `get_session()` context manager — rollback only happens if the test raises. Successful tests simply close without explicit rollback; uncommitted mutations are lost on session close. `seeded_session` fixture (module-scoped) explicitly rolls back on teardown for zero side effects between modules. 30+ test files total.

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

## Techno Kids — Business Reports Context Document

**Purpose:** This document captures the discussion, decisions, and finalized query logic for four business reports, based on the live Supabase database (`techno-future-auth`, project ID `srbppkcvrgioneitktdj`).

---

## 1. Background

The original schema document (v2 — Simplified) provided at the start of this chat was **out of date**. The live database has evolved significantly. Key differences discovered by querying Supabase directly:

| Area | Documented schema | Actual live schema |
|---|---|---|
| Student status | Only `is_active BOOLEAN` | Real enum `student_status`: `active`, `waiting`, `inactive` — plus `waiting_since`, `waiting_priority`, `waiting_notes` |
| Deletion | Hard `is_active` flag | Proper soft delete via `deleted_at` / `deleted_by` on `students` and `payments` |
| Levels/rounds | Tracked via `groups.session_count` + `level_number` | Moved to a dedicated `group_levels` table (one row per round of a group), with its own `instructor_id`, `sessions_planned`, `status`, `effective_from/to` |
| Payments | Single flat ledger | `payments` now has `transaction_type` (`charge` / `payment` / `refund`), linked via `receipts`, with soft delete |
| Employees | `part_time` / `contract` only | Also includes `full_time` |
| New tables not in original doc | — | `parents`, `student_parents`, `group_course_history`, `enrollment_level_history`, `student_activity_log`, `notification_templates`, `notification_logs`, `admin_notification_settings`, `notification_additional_recipients`, `audit_logs`, `receipts` |

**Takeaway:** Always verify against the live schema before building reports — the written documentation lags behind the actual product.

---

## 2. Report Definitions (as agreed)

### Report 1 — New Customers
**Definition:** Students newly registered in the system, grouped by month (`students.created_at`).

```sql
SELECT date_trunc('month', created_at)::date AS month, count(*) AS new_customers
FROM students
WHERE deleted_at IS NULL
GROUP BY 1
ORDER BY 1;
```

**Validated output (live data):** May 2026 → 162, June 2026 → 494, July 2026 (partial) → 33.

---

### Report 2 — Old Customers
**Definition (agreed):** Students whose **first enrollment** falls in the earliest available cohort — currently, before June 1, 2026 (i.e., the May 2026 cohort, since the system's data only goes back to May 2026).

Notes:
- Original idea of "12+ months tenure" was dropped — the system only has ~2 months of history, so that threshold would return zero results.
- "Returning after a gap" logic was also dropped per your instruction — gap length is being ignored for this version of the report.
- This definition should be **revisited periodically** as more history accumulates (e.g., switch to "12+ months since first enrollment" once the business has a full year of data).

```sql
SELECT s.id, s.full_name, s.phone, MIN(e.enrolled_at) AS first_enrollment
FROM students s
JOIN enrollments e ON e.student_id = s.id
WHERE s.deleted_at IS NULL
GROUP BY s.id, s.full_name, s.phone
HAVING MIN(e.enrolled_at) < '2026-06-01'
ORDER BY first_enrollment;
```

**Validated output (live data):** 147 students currently qualify.

---

### Report 3 — New Waiting Students Every Month
**Definition:** Count of students with `status = 'waiting'`, grouped by the month they entered waiting status (`waiting_since`).

**⚠️ Blocking issue found — requires an app fix:**
- `waiting_since` is currently `NULL` for **all 303** waiting students. The column exists but the app never sets it.
- Falling back to `created_at` doesn't work either: 297 of the 303 waiting students share the exact same `created_at` month (June 2026), which is almost certainly a bulk import/migration, not organic monthly signups.
- **Action needed:** update the app so that whenever a student's `status` is changed to `'waiting'`, it sets `waiting_since = now()`. Once that's live, this report will be accurate for all data going forward. Historical months before the fix will remain unreliable and should probably be excluded or footnoted in the report.

```sql
-- Usable once waiting_since is populated going forward
SELECT date_trunc('month', COALESCE(waiting_since, created_at))::date AS month, count(*) AS new_waiting
FROM students
WHERE status = 'waiting' AND deleted_at IS NULL
GROUP BY 1
ORDER BY 1;
```

---

### Report 4 — Round Cost
**Definition (agreed):** For each "round" (a row in `group_levels`, representing one level/cycle of a group) taught by a **contract** instructor, the cost = revenue collected for that round × the instructor's `contract_percentage`.

Scope decisions:
- **Contract instructors only.** Part-time instructors' fixed `monthly_salary` is explicitly **excluded** from this report — that will be a separate report later.
- Revenue = actual cash collected, not just billed amount. Currently `payments.transaction_type` only contains `'payment'` rows (no charges/refunds recorded yet), so revenue = `SUM(payments.amount)` joined via `enrollment_id`.
- Instructor for a round is taken from `group_levels.instructor_id` (falls back to `groups.instructor_id` if null, to handle any rounds not yet backfilled).

```sql
WITH level_revenue AS (
  SELECT gl.id AS group_level_id, gl.group_id, gl.level_number,
         COALESCE(gl.instructor_id, g.instructor_id) AS instructor_id,
         COALESCE(SUM(p.amount), 0) AS revenue_collected
  FROM group_levels gl
  JOIN groups g ON g.id = gl.group_id
  LEFT JOIN enrollments e ON e.group_id = gl.group_id AND e.level_number = gl.level_number
  LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL AND p.transaction_type = 'payment'
  GROUP BY gl.id, gl.group_id, gl.level_number, COALESCE(gl.instructor_id, g.instructor_id)
)
SELECT lr.group_level_id, c.name AS course, lr.level_number, emp.full_name AS instructor,
       lr.revenue_collected, emp.contract_percentage,
       ROUND(lr.revenue_collected * emp.contract_percentage / 100, 2) AS round_cost
FROM level_revenue lr
JOIN groups g ON g.id = lr.group_id
JOIN courses c ON c.id = g.course_id
JOIN employees emp ON emp.id = lr.instructor_id
WHERE emp.employment_type = 'contract'
ORDER BY lr.group_level_id;
```

**Validated example:** Mariam Mohamed Tawfik's EV3 round collected 2,750 EGP in payments → at her 25% contract rate, round cost = 687.50 EGP.

---

## 3. Open Items / Follow-ups

1. **App fix required** for Report 3: set `students.waiting_since = now()` on transition to `waiting` status.
2. **Part-time instructor cost report** — separate report to be scoped later (salary allocation across groups/rounds taught per month — not yet designed).
3. **"Old customers" threshold** should be revisited as the business accumulates more than a few months of history; the current May-2026-cohort definition is a placeholder tied to the system's short data history.
4. Decide whether to formalize these four queries as **Postgres views** (e.g., `v_new_customers`, `v_old_customers`, `v_waiting_students_monthly`, `v_round_cost`) so the app/dashboard can query them directly — this was proposed but not yet actioned.

---

## 4. Data Snapshot (at time of this session)

- `students`: 689 total rows — 386 `active`, 303 `waiting`, 0 currently `inactive`
- `employees`: 3 `full_time`, 7 `contract`, 7 `part_time`
- `enrollments`: 678 rows, spanning May 3, 2026 → July 8, 2026
- `payments`: 387 rows, all `transaction_type = 'payment'` (no charges/refunds recorded yet), totaling 234,502 EGP

<!-- SPECKIT START -->
Active plan: `specs/031-unified-student-listing-dto/plan.md`
<!-- SPECKIT END -->
