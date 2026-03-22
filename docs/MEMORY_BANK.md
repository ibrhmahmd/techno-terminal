# Techno Kids CRM — Memory Bank
> **Purpose:** Complete architectural and code-level reference for AI agent handoff.  
> **Last updated:** 2026-03-22  
> **Schema version:** v3.3 (15 tables, 5 views) — see `db/schema.sql` header  
> **Framework:** Streamlit + FastAPI + SQLModel + PostgreSQL + Supabase Auth  

---

## 1. Project Overview

**Techno Kids CRM** is a full-stack internal management system for a STEM education center. It manages:
- Student & parent (guardian) registration and profiles
- Course catalogs, group scheduling, and session tracking
- Student enrollment per group level
- Attendance marking
- Financial receipts and payment tracking (with discounts and refunds)
- Competition registration (teams, categories, fees)
- Analytics and activity reporting dashboards
- Staff (employee) directory and linked login accounts

**Transports (dual path):**
- **Streamlit** (`app/ui/`) is the primary internal UI. Pages call **`app/modules/*/service.py` directly** (same process, no HTTP to self for domain data).
- **FastAPI** (`app/api/`) exposes a growing **REST API** (JSON). It reuses the same services and `get_session`-backed repositories. **Routers are not yet mounted for most domains** — `GET /api/v1/auth/me` is the main wired surface today. Streamlit stores `access_token` in session state after Supabase login for **Bearer** API calls.

**Authentication:** End-user credentials are verified by **Supabase** (`sign_in_with_password` in Streamlit; JWT verification via Supabase SDK in FastAPI). Local Postgres `users` rows map identities with `supabase_uid`. After successful Streamlit login, **`update_last_login`** updates `users.last_login`.

---

## 2. Repo Structure

```
project_root/
├── run_ui.py                     # Entry point — seeds admin (Supabase), runs Streamlit on app/ui/main.py
├── run_api.py                    # Uvicorn bootloader for FastAPI (port 8000, reload)
├── .env                          # DATABASE_URL, SUPABASE_* (not committed)
├── .env.example                  # Template for required env vars
├── pyproject.toml                # Project metadata (package discovery for `app*`)
├── requirements.txt              # streamlit, sqlmodel, fastapi, supabase, alembic, pydantic-settings, …
├── alembic.ini                   # Alembic config (revisions under alembic/versions/)
├── alembic/
│   ├── env.py                    # Loads DATABASE_URL + all SQLModel metadata
│   └── versions/                 # e.g. 001_baseline_schema_v33 (empty upgrade; baseline = schema.sql)
├── db/
│   ├── README.md                 # Hybrid workflow: schema.sql vs migrations vs Alembic stamp
│   ├── schema.sql                # Full DDL v3.3 (canonical for greenfield psql)
│   └── migrations/
│       ├── README.md             # Order of hand-written SQL upgrades
│       ├── supabase_auth_patch.sql   # Legacy: password_hash → supabase_uid
│       └── 002_users_supabase_roles_v33.sql  # Role CHECK + column alignment for old DBs
├── docs/
│   ├── MEMORY_BANK.md            # THIS FILE (handoff summary)
│   ├── plans/                    # Short summaries of completed engineering plans (see §12)
│   └── memory_bank/              # Deeper specs, ADRs, reviews, ETL history (see §12)
└── app/
    ├── core/
    │   ├── config.py             # Pydantic Settings: database_url, supabase_url, supabase_anon_key, optional service_role
    │   └── supabase_clients.py   # get_supabase_anon(), get_supabase_admin() (lazy; admin needs service role)
    ├── api/
    │   ├── main.py               # FastAPI app factory, CORS, router mounts
    │   ├── dependencies.py       # get_db, get_current_user (HTTPBearer JWT → Supabase verify → local User)
    │   ├── exceptions.py         # HTTP exception registration
    │   └── routers/
    │       └── auth.py           # e.g. GET /me (Bearer JWT)
    ├── db/
    │   ├── connection.py         # SQLModel engine + get_session() context manager
    │   ├── seed.py               # Supabase-linked admin seed (needs service role)
    │   └── init_db.py            # Optional: drop/create ORM tables + recreate views + seed
    ├── modules/                  # Domain modules — layered (models → repo → service)
    │   ├── auth/
    │   ├── hr/
    │   ├── crm/
    │   ├── academics/
    │   ├── enrollments/
    │   ├── attendance/
    │   ├── finance/
    │   ├── competitions/
    │   └── analytics/
    ├── shared/
    │   ├── base_repository.py    # RepositoryProtocol (structural typing)
    │   ├── constants.py          # MIN_PASSWORD_LENGTH, domain literals
    │   ├── validators.py
    │   └── exceptions.py
    └── ui/
        ├── main.py               # Sidebar page_link entries + auth guard
        ├── state.py              # Session state helpers
        ├── pages/                # Streamlit numbered pages
        └── components/           # Reusable UI fragments (incl. employee/, forms/, charts/)
```

---

## 3. Database Architecture

### 3.1 Connection (`app/db/connection.py`)

```python
get_engine()      # Lazy singleton SQLAlchemy engine from DATABASE_URL
get_session()     # @contextmanager — yields Session, auto-commit on exit, rollback on exception
                  # CRITICAL: expire_on_commit=False so objects are usable after the session closes
```

**Connection pool config:** `pool_size=5`, `max_overflow=5`, `pool_timeout=30`, `pool_recycle=1800`

### 3.2 Schema Overview (15 tables, dependency order)

| Table | Purpose | Key Constraints |
|---|---|---|
| `guardians` | Parent/guardian contact records | phone_primary indexed |
| `employees` | Staff (instructors, admin) | `employment_type IN ('full_time','part_time','contract')` — see `app/modules/hr/` |
| `users` | Login accounts | roles: `admin`, `instructor`, `system_admin`; `supabase_uid` UNIQUE NOT NULL; optional `employee_id` → `employees` |
| `students` | Student profiles | `is_active` flag; no guardian FK — uses junction table |
| `student_guardians` | M:M student–guardian with primary flag | `UNIQUE(student_id, guardian_id)` |
| `courses` | Course catalog | `category IN ('software','hardware','steam','other')` |
| `groups` | Scheduling groups per course | `level_number` tracks current level; `status IN ('active','completed','cancelled')` |
| `sessions` | Individual class sessions | `ON DELETE RESTRICT` on `group_id` — cannot delete group with sessions |
| `enrollments` | Student enrolled in a group level | Partial UNIQUE: one active enrollment per (student, group); `status IN ('active','completed','transferred','dropped')` |
| `attendance` | Attendance per session | `UNIQUE(student_id, session_id)`; `enrollment_id` NOT NULL |
| `receipts` | Payment receipt header | `payment_method IN ('cash','card','transfer','online')` |
| `payments` | Payment line items | `transaction_type IN ('charge','payment','refund')`; `amount != 0` (allows negative refund) |
| `competitions` | Competition events | |
| `competition_categories` | Categories within a competition | `ON DELETE CASCADE` from competition |
| `teams` | Team per category | `enrollment_fee_per_student` can be NULL or float > 0 |
| `team_members` | Students in teams | `UNIQUE(team_id, student_id)`; `fee_paid BOOLEAN` |

### 3.3 Views (5)

| View | What it gives you |
|---|---|
| `v_students` | students + primary guardian name/phone joined |
| `v_enrollment_balance` | enrollment_id + `net_due`, `total_paid`, balance (live, computed from payments) |
| `v_enrollment_attendance` | enrollment_id + `sessions_attended`, `sessions_missed` |
| `v_siblings` | pairs of students who share a guardian |
| `v_group_session_count` | group_id + level → `regular_sessions`, `extra_sessions`, `total_sessions` |

> **Critical:** `v_enrollment_balance.balance` is a PostgreSQL `Decimal` — always cast to `float()` in Python before arithmetic.

### 3.4 `users` table and Supabase (v3.3)

- **`db/schema.sql` v3.3** defines `users` with **`supabase_uid`** (no `password_hash`) and role **`CHECK (admin, instructor, system_admin)`**.
- **Canonical roles in code:** `app/modules/auth/role_types.py` (`UserRole`, `ALL_ROLE_VALUES`, `is_valid_role`) — keep in sync with the DB CHECK when adding a role.
- **Upgrading old databases:** See `db/migrations/README.md` (`002_users_supabase_roles_v33.sql` + legacy `supabase_auth_patch.sql`). Backfill `supabase_uid` before enforcing `NOT NULL` where documented.
- **Greenfield + Alembic:** After `psql -f db/schema.sql`, run `alembic stamp 001_baseline_v33` so revision history matches reality (`db/README.md`, `alembic/README.md`).

### 3.5 JSONB `metadata` columns (ORM vs SQL)

Several tables use a PostgreSQL column named **`metadata`**. SQLAlchemy reserves `metadata` on declarative models, so ORM attributes use distinct Python names mapping to that column:

| Table (SQL) | Model attribute (Python) | Module |
|-------------|----------------------------|--------|
| `employees` | `employee_metadata` | `hr_models` |
| `students` | `profile_metadata` | `crm_models` |
| `groups` | `group_metadata` | `academics_models` |
| `enrollments` | `enrollment_metadata` | `enrollment_models` |
| `payments` | `payment_metadata` | `finance_models` |
| `teams` | `team_metadata` | `competition_models` |

---

## 4. Module Architecture

Each domain module follows a **3-layer pattern**:

```
*_models.py     SQLModel ORM classes (table=True) — file name is usually prefixed (e.g. crm_models.py)
repository.py   Pure data access — accepts Session, returns ORM objects or dicts
service.py        Business logic — opens sessions via get_session(), calls repo, raises ValueError on validation failure
```

**Variations:**
- **Academics:** session entity lives in `academics_session_models.py` (`CourseSession`), not in `academics_models.py`, to avoid circular imports.
- **API DTOs:** several modules expose `*_schemas.py` (Create/Read shapes) for FastAPI — alongside `*_models.py`.
- **`app/shared/base_repository.py`:** `RepositoryProtocol` for structural typing; repos may expose module-level aliases (e.g. `get_by_id`) without class inheritance.

The UI imports **only from `service.py`**, not from `repository.py`.

---

## 5. Module Reference

### 5.1 `app/modules/auth` (Supabase)

**Models (`auth_models.py`):** `User` (table), `UserBase`, `UserCreate` (optional `supabase_uid` until after Supabase signup), `UserRead`, **`UserPublic`** (no `supabase_uid` — use for JSON APIs).

**Roles:** `role_types.py` — `UserRole` enum / `is_valid_role`; `UserBase.role` validated against `ALL_ROLE_VALUES`.

**`auth_repository.py`:** `get_user_by_username`, `get_user_by_supabase_uid`, `get_users_by_employee_id`, `get_user_by_id`, `create_user`, `update_last_login`, `update_user`, …

**`auth_service.py`:** `get_user_by_supabase_uid`, `get_user_by_username`, `update_last_login`, `get_users_for_employee`, `force_reset_password` (Supabase admin), `link_employee_to_new_user` (Supabase admin + local `User` row).

**`auth_schemas.py`:** Placeholder Pydantic bodies for future routes (e.g. `PasswordResetBody`).

**Auth API (`app/api/dependencies.py`):**
- **`HTTPBearer`** (not OAuth2 password flow) — raw JWT from Supabase.
- `get_current_user` → `get_supabase_anon().auth.get_user(token)` → `get_user_by_supabase_uid` → local `User`; **403** if `is_active` is false; failures logged without logging the token.

**`app/api/routers/auth.py`:** `GET /api/v1/auth/me` returns **`UserPublic`** (omits `supabase_uid`).

---

### 5.1.B `app/modules/hr` (Staff Management)

**Models:** `Employee` (`hr_models.py`)

**service / repository:** Employee directory lifecycle; **`create_staff_account(EmployeeCreate, UserCreate, password)`** creates Supabase user then `Employee` + `User` in one transaction path; **`update_staff_account`** validates role via `is_valid_role`. Uses **`get_supabase_admin()`** only when needed (service role key required).

---

### 5.2 `app/modules/crm` — Students & Guardians

> **Naming:** DB/model = `guardians` / `Guardian`. UI text = "Parent". Python APIs keep `guardian` in function names.

**Models:** `Guardian`, `Student`, `StudentGuardian` (`crm_models.py`)

**repository.py:** `create_guardian`, `get_guardian_by_id`, `get_guardian_by_phone`, `search_guardians`, `create_student`, `get_student_by_id`, `search_students`, `get_student_guardians`, `link_guardian`, `get_siblings`, …

**service.py:** `validate_phone`, `register_guardian`, `find_or_create_guardian`, `search_guardians`, `register_student`, `search_students`, `find_siblings`, `get_guardian_students`, …

---

### 5.3 `app/modules/academics` — Courses & Groups

**Models:** `Course`, `Group` (`academics_models.py`); **`CourseSession` in `academics_session_models.py` (not `academics_models.py`).**

**Important field name:** `Group.level_number` is the group's current active level. NOT `current_level`.

**Service time window constraint:** Groups must be scheduled between **11:00 AM and 9:00 PM**.

**service.py (representative):** `add_new_course`, `update_course_price`, `get_active_courses`, `schedule_group`, `get_groups_by_course`, `get_all_active_groups`, `get_all_active_groups_enriched`, `get_todays_groups_enriched`, `get_group_by_id`, `generate_level_sessions`, `add_extra_session`, `delete_session`, `mark_substitute_instructor`, `list_group_sessions`, `check_level_complete`, `advance_group_level`, …

---

### 5.4 `app/modules/enrollments`

**Model:** `Enrollment` — `enrollment.level_number` is a **snapshot** of `group.level_number` at enrollment time.

**service.py:** `enroll_student`, `get_student_enrollments`, `get_group_enrollments`, `transfer_enrollment`, `drop_enrollment`, …

---

### 5.5 `app/modules/attendance`

**Valid statuses:** `present`, `absent`, `late`, `excused`  
`unmarked` is a **virtual** UI status when no attendance row exists.

**service.py:** `mark_attendance`, `get_session_attendance`, `get_student_attendance`, …

---

### 5.6 `app/modules/finance`

**Models:** `Receipt`, `Payment`  
**transaction_type:** `payment`, `charge`, `refund`  
**payment_type:** `course_level`, `competition`, `other`  
**Auto receipt_number format:** `REC-{year}-{zero-padded-id}`

**service.py:** `open_receipt`, `add_charge_line`, `finalize_receipt`, `refund_receipt`, `get_receipt_with_lines`, `get_student_balance`, `get_guardian_receipts`, `search_receipts`, …

---

### 5.7 `app/modules/competitions`

**Models:** `Competition`, `CompetitionCategory`, `Team`, `TeamMember`  
**Hierarchy:** Competition → Category → Team → TeamMember

**service.py:** `get_student_competitions`, `create_competition`, `list_competitions`, category/team CRUD, `add_member_to_team`, `remove_member_from_team`, `mark_team_fee_paid`, …

---

### 5.8 `app/modules/analytics`

All functions return `list[dict]` or scalars. Always `float()` cast monetary columns.

**repository.py:** Raw SQL via `text()` — `get_active_enrollment_count`, `get_today_sessions`, `get_today_unpaid_attendees`, `get_revenue_by_date`, `get_revenue_by_method`, `get_outstanding_by_group`, `get_top_debtors`, `get_group_roster`, `get_attendance_heatmap`, `get_competition_fee_summary`, …

**service.py:** Same public names; each opens its own `get_session()` and calls the repo.

---

## 6. UI Architecture

### 6.1 Sidebar navigation (`app/ui/main.py`)

Explicit **`st.page_link`** entries (primary IA):
- Dashboard → `pages/0_Dashboard.py`
- Directory → `pages/1_Directory.py`
- Competitions → `pages/8_Competitions.py`
- Reports → `pages/9_Reports.py`

Streamlit still discovers **other scripts** under `app/ui/pages/` (numbered filenames). They are reachable via the **multipage sidebar** (depending on Streamlit version/settings) and via **`st.switch_page`** from components.

### 6.2 Session state navigation pattern

```python
# Sender:
st.session_state["nav_target_student_id"] = student.id
st.switch_page("pages/1_Directory.py")

# Receiver (Directory): routes to student detail when key is set
if "nav_target_student_id" in st.session_state:
    render_student_detail(st.session_state.pop("nav_target_student_id"))
```

**Active navigation / session keys:**

| Key | Used by |
|---|---|
| `nav_target_student_id` | Student detail (Directory + cross-links) |
| `nav_target_parent_id` | Parent/guardian detail (Directory) |
| `nav_target_group_id` | Group-focused flows (legacy naming; some pages use `selected_group_id` from Dashboard) |
| `nav_target_course_id` | Course detail |
| `selected_receipt_id` | Finance receipt detail inside Dashboard tab |
| `user` | Auth session — set after successful login |
| `access_token` | Supabase JWT — stored for future API calls |

### 6.3 Pages (actual filenames)

| File | Role | How reached |
|---|---|---|
| `0_Dashboard.py` | KPIs, today's sessions → group navigation, **Financial Desk** tab (`finance_overview` / receipts), **Quick Registration** | Sidebar |
| `1_Directory.py` | Tabs: Parents, Students; detail views via `nav_target_*` | Sidebar |
| `3_Course_Management.py` | Courses | Multipage / in-app |
| `4_Group_Management.py` | Groups, sessions, attendance | From Dashboard session row, course detail, etc. |
| `5_Enrollment.py` | Enrollment / transfers | From student detail, etc. |
| `6_Staff_Management.py` | Staff directory + add employee | Multipage (not in custom sidebar list) |
| `8_Competitions.py` | Competitions | Sidebar |
| `9_Reports.py` | Multi-tab reports + heatmaps | Sidebar |
| `login.py` | Supabase-backed login | `auth_guard` redirect |

### 6.4 Components (selected)

| Area | Files |
|---|---|
| Auth | `auth_guard.py` — `require_auth()` |
| CRM / profiles | `parent_overview.py`, `parent_detail.py`, `student_overview.py`, `student_detail.py` |
| Academics | `course_overview.py`, `course_detail.py`, `group_overview.py`, `group_detail.py`, `attendance_grid.py` |
| Finance | `finance_overview.py`, `finance_receipt.py` |
| Competitions | `competition_overview.py`, `competition_detail.py` |
| Staff | `employee/employee_directory.py`, `employee_detail.py`, `employee_form.py` — use `hr_service` + `auth_service` (`get_users_for_employee`, `create_staff_account`, `update_staff_account`, `force_reset_password`, `link_employee_to_new_user`); roles from `UserRole` |
| Dashboard | `quick_register.py` |
| Reports | `charts/*.py` (e.g. retention, utilization, instructor matrix) |
| Forms | `forms/edit_*.py` |

---

## 7. FastAPI snapshot (`app/api/`)

- **`create_app()`** in `main.py` — title *Techno Future API*, **CORS open** (`allow_origins=["*"]`) for development.
- **Routers:** `auth` mounted at `/api/v1/auth` — **`GET /api/v1/auth/me`** — `Authorization: Bearer <supabase_jwt>` — response **`UserPublic`**.
- **`GET /health`** — liveness check.
- **`get_db`** — yields a `Session` scoped to the request (uses `get_session()` context manager pattern).
- **Exception handlers:** `app/api/exceptions.py`

Further domain routers are **planned** (see `docs/memory_bank/04_architecture/09_phase5_api_technical_plan.md`); commented placeholders may exist in `main.py`.

---

## 8. Architectural Decision Records

| # | Decision | Rationale |
|---|---|---|
| ADR-1 | Streamlit as primary internal UI; FastAPI API added for scale / future clients | Internal ops stay simple; JSON API for mobile/web clients without duplicating business logic |
| ADR-2 | SQLModel (not raw SQLAlchemy only) | Pydantic validation + SQLAlchemy in one |
| ADR-3 | `get_session()` as context manager | Auto-commit on exit, rollback on exception; `expire_on_commit=False` |
| ADR-4 | `enrollment.level_number` is a snapshot | Historical enrollments stay stable when group advances |
| ADR-5 | `student_guardians` junction | M:M parents; sibling detection via `v_siblings` |
| ADR-6 | Receipts + Payment lines | One receipt, many students; refunds as new rows |
| ADR-7 | NULL/zero-fee teams auto-mark paid | Academy-sponsored teams |
| ADR-8 | Guardian (code) vs Parent (UI) | Avoid breaking imports; consistent UX wording |
| ADR-9 | Analytics raw SQL (`text()`) | Aggregations and window functions stay readable |
| ADR-10 | Supabase for identity | Centralized auth; local `users.supabase_uid` mapping |
| ADR-11 | Canonical `UserRole` in code + DB CHECK | Single extensibility path for roles (`role_types.py` + migrations) |
| ADR-12 | Hybrid DB workflow | `db/schema.sql` for full DDL; `db/migrations/*.sql` for ops upgrades; Alembic for revision tracking |

---

## 9. Standard Workflows

### Finance Flow
```
1. open_receipt(guardian_id, method, user_id)        -> Receipt
2. add_charge_line(receipt_id, student_id, ...)      -> Payment (repeat per student)
3. finalize_receipt(receipt_id)                      -> dict summary
4. (Competition) mark_team_fee_paid(team_id, ...)
5. (Refund) refund_receipt(receipt_id, reason)       -> mirror rows, no deletion
```

### Enrollment Flow
```
1. search_students(query)                            -> pick student
2. get_all_active_groups()                           -> pick group
3. UI shows amount_due (defaults to course.price_per_level)
4. enroll_student(student_id, group_id, ...)         -> (Enrollment, capacity_exceeded: bool)
5. Record payment via Finance module against enrollment_id
```

---

## 10. Common Pitfalls

1. **`Decimal` + `float` crash** — cast `float(value)` before arithmetic on money from the DB.
2. **`group.current_level` does NOT exist** — use `group.level_number`.
3. **`search_Parents` / `list_groups` do NOT exist** — use `search_guardians`, `get_all_active_groups()`, etc.
4. **Session state navigation** — prefer `.pop("nav_key")` when consuming one-shot navigation ids.
5. **`st.switch_page()` path** — must match the filename under `pages/` (e.g. `"pages/1_Directory.py"`, `"pages/0_Dashboard.py"`).
6. **`expire_on_commit=False`** — objects stay usable after close; do not share across threads.
7. **Zero-fee teams** — `enrollment_fee_per_student is None or == 0` → treat as paid where applicable.
8. **`CourseSession` location** — `academics_session_models.py`, not `academics_models.py`.
9. **`session` parameter name** — in repos, `session` is the **SQLModel DB session**, not HTTP session.
10. **Analytics DataFrames** — rename columns by **name**, not by positional index.
11. **`db/schema.sql` v3.3** — `users` matches ORM for Supabase auth; use `db/migrations/` for older DBs (§3.4).
12. **Refactoring backlog doc** — `docs/memory_bank/05_reviews/refactoring_backlog.md` predates the populated `app/api/` tree; use this MEMORY_BANK + code for current layout.

---

## 11. Dev Environment

```bash
# UI (seeds admin via Supabase when configured)
python run_ui.py

# API
python run_api.py
# or: uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

# Optional: ORM-first DB reset (destructive) + views + seed
python -m app.db.init_db

# Schema from SQL file (destructive re-run)
psql $DATABASE_URL -f db/schema.sql
# Then stamp Alembic baseline (no DDL from Alembic for 001):
alembic stamp 001_baseline_v33

# Upgrading legacy DBs (see db/migrations/README.md):
# psql $DATABASE_URL -f db/migrations/supabase_auth_patch.sql
# psql $DATABASE_URL -f db/migrations/002_users_supabase_roles_v33.sql

# Windows venv
.venv\Scripts\activate
```

**Environment variables (minimum):**
- `DATABASE_URL` — PostgreSQL
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — login + JWT verification
- `SUPABASE_SERVICE_ROLE_KEY` — **required** for `seed_admin_account()`, staff account creation, and `force_reset_password` (Supabase Admin API); optional only for read-only dev without HR auth actions

**Key dependencies (`requirements.txt`):**
- `streamlit`, `pandas` (Dashboard/Reports)
- `sqlmodel`, `psycopg2-binary`, `alembic`
- `python-dotenv`
- `fastapi`, `uvicorn`, `python-multipart`, `httpx`, `python-jose[cryptography]`
- `supabase`
- `pydantic-settings` — `app/core/config.py`

---

## 12. Phase History & Related Docs

| Phase | Features Added |
|---|---|
| 1 | DB schema, student/guardian CRUD |
| 2 | Course catalog, groups, session generation |
| 3 | Enrollment with level snapshots |
| 4 | Finance: receipts, payments, balances |
| 5 | Competitions; parent profile competition fees |
| 5 Polish | Competition inline edit/delete; Parent UI wording; wide layout |
| 6 | Analytics; Dashboard; Reports tabs; exports |
| 7 | FastAPI scaffold, Supabase JWT deps, `run_api`, auth `/me`, HR + staff UI, Directory consolidation |
| 8 | Auth hardening: `UserRole`, `UserPublic`, `HTTPBearer`, lazy Supabase clients; schema v3.3; JSONB metadata on models; `db/migrations/002`, Alembic baseline; employee UI wired to services |

**Completed plan write-ups:** `docs/plans/` ([README](plans/README.md)) — memory-bank refresh summary, auth/DB alignment task list.

**See also (longer-form, may predate code):**
- `docs/plans/` — archived summaries of completed engineering plans  
- `docs/memory_bank/01_business_domain/` — requirements, data dictionary, project origin  
- `docs/memory_bank/02_database_design/` — schema narrative  
- `docs/memory_bank/03_etl_pipeline/` — **historical** Excel ETL context (no `src/` pipeline in this repo snapshot)  
- `docs/memory_bank/04_architecture/` — phased technical plans, session management, API plan  
- `docs/memory_bank/05_reviews/` — architecture / SaaS reviews, refactoring backlog  

---

## 13. Documentation drift policy

When the repo and `docs/memory_bank/*` disagree, **treat this `MEMORY_BANK.md` and the code as authoritative** for agents; use subdocs for background and intent, then verify against `app/` and `db/`.
