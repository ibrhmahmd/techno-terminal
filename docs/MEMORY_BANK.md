# Techno Terminal — Memory Bank
>
> **Purpose:** Complete architectural and code-level reference for AI agent handoff.  
> **Last updated:** 2026-04-12  
> **Schema version:** v3.4 (30 tables, 12 views) — verified via Supabase  
> **Framework:** Streamlit + FastAPI + SQLModel + PostgreSQL + Supabase Auth  

---

## 1. Project Overview

**Techno Terminal** is a full-stack internal management system for a STEM education center. It manages:

- Student & parent (parent) registration and profiles
- Course catalogs, group scheduling, and session tracking
- Student enrollment per group level
- Attendance marking
- Financial receipts and payment tracking (with discounts and refunds)
- Competition registration (teams, categories, fees)
- Analytics and activity reporting dashboards
- Staff (employee) directory and linked login accounts

**Transports (dual path):**

- **Streamlit** (`app/ui/`) is the primary internal UI. Pages call **`app/modules/*/service.py` directly** (same process, no HTTP to self for domain data).
- **FastAPI (API) Snapshot** (`app/api/`):
  - **Router Structure:** Split packages for `analytics/`, `academics/`, `crm/` domains (no monolithic routers)
  - **DTOs:** All responses typed with Pydantic (no `list[dict]` or `Any`)
  - **DI Pattern:** All services available via `Depends()` factories in `dependencies.py`
  - **Error Handling:** Standardized `ErrorResponse` envelope via custom + HTTPException handlers
  - **Auth:** Supabase JWT verification with role-based access (admin, system_admin only)
  - **Phase 5.2–5.5:** CRM, academics, transactions, analytics routers fully implemented

**April 2026 — Role System Simplification:**
- **Simplified roles:** Reduced from 4 roles (admin, instructor, receptionist, manager) to 2 roles (admin, system_admin)
- **Rationale:** Eliminate complexity; all operations now require admin access
- **API Guards:** `require_admin` (admin + system_admin), `require_any` (any authenticated user)
- **Attendance:** Now requires admin access (was instructor-only)
- **Files changed:** `app/modules/auth/constants.py`, `app/api/dependencies.py`, `app/api/routers/attendance_router.py`
- **Breaking change:** Users with instructor/receptionist/manager roles will need role updated to admin

**Authentication:** End-user credentials are verified by **Supabase** (`sign_in_with_password` in Streamlit; JWT verification via Supabase SDK in FastAPI). Local Postgres `users` rows map identities with `supabase_uid`. After successful Streamlit login, **`update_last_login`** updates `users.last_login` (explicit `session.commit()` in service; `get_session()` also commits on exit).

**Current Status (April 2026):**

- **API Finalization Complete (2026-04-02):** All auth, session, competition, and finance endpoints implemented. The backend is **100% ready for frontend consumption**.
- **Testing Initiative Complete (2026-04-12):** 94% coverage (75/80 endpoint scenarios). All 10 phases complete.
  - **Test Files:** 20 test modules with 161 tests (160 passing)
  - **Coverage:** Auth (6/6), CRM (9/9), Enrollments (4/4), Finance (8/8), Attendance (2/2), Academics (14/14), Competitions (8/8), HR (7/7), Analytics (16/16)
  - **Strategy:** Phased testing with transaction isolation, JWT mocking, and dependency-based test fixtures
- **Auth Endpoints:** `POST /auth/login`, `POST /auth/logout`, `POST /auth/refresh`, `GET /auth/me`, `POST /auth/users`, `POST /auth/users/{id}/reset-password` — all using Supabase `sign_in_with_password`.
- **Daily Schedule Endpoint:** `GET /academics/sessions/daily-schedule?day={dayName}` — single high-performance join across `CourseSession`, `Group`, `Course`, `Enrollment` for the Dashboard.
- **Competitions Module:** Promoted from stub to full CRUD with registration, categories, and fee bypass endpoints.
- **PDF Export Enhancement (B4 ✅):** `GET /finance/receipts/{id}/pdf` now returns a branded A4 PDF with optional logo (env: `PDF_LOGO_PATH`), company address, and dual signature blocks.
- **Frontend Plan:** Stack and phase-by-phase build order documented in `docs/planning/FRONTEND_PLAN.md`. Stack: **Vite + React 18 + TypeScript + TanStack Query + Zustand + React Router v6**.
- **Backlog Streams A & B:** Fully complete. Stream C (technical debt) deferred post-delivery.

**Previous Status (End of March 2026):**

- **Streamlit Stabilization Complete:** All UI crashes caused by the deep-SOLID architecture (Pydantic DTO strictness, Service facades) have been patched.
- **Pivot:** API scaffolding (Day 2 of Delivery Plan) is temporarily paused. The project is currently entering a new structural sprint to decouple the Student-Parent relationship, shift financial tracking directly to the Student entity, handle automatic level progression, and handle session cancellations with cascading numbering.

**Audit (D4):** `app/shared/audit_utils.py` stamps `created_at` / `updated_at` / optional `created_by` on CRM, enrollments, and academics mutating paths where applicable. **`db/migrations/005_audit_d4_timestamps.sql`** backfills NULLs, sets `DEFAULT CURRENT_TIMESTAMP`, normalizes legacy TEXT `sessions.created_at` / `session_date`, and adds `tf_set_updated_at` triggers (mirrored in greenfield `db/schema.sql`). Streamlit uses **`state.get_current_user_id()`** for `created_by` / `received_by`. See `docs/planning/sprint_roadmap_post_qa_2026.md` Sprint 3.

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
│       ├── 002_users_supabase_roles_v33.sql  # Role CHECK + column alignment for old DBs
│       ├── 003_employees_employment_full_time.sql  # employees.employment_type includes full_time
│       ├── 004_employees_sprint2_identity.sql      # national_id, education fields, uniqueness (Sprint 2)
│       ├── 005_audit_d4_timestamps.sql             # D4: audit backfill, DEFAULTs, updated_at triggers
│       ├── 006_receipts_paid_at_index.sql          # B9: idx_receipts_paid_at (Sprint 4)
│       └── 007_p6_enrollment_balance.sql           # B8/P6: account balance sign convention
├── docs/
│   ├── MEMORY_BANK.md            # THIS FILE (handoff summary)
│   ├── archive/                  # Legacy history, completed refactors, and old plans
│   ├── planning/                 # Active sprint planning, QA backlogs, and roadmaps
│   └── memory_bank/              # Deeper specs, ADRs, reviews, ETL history (see §12)
└── app/

    ├── core/
    │   ├── config.py             # Pydantic Settings: database_url, supabase_url, supabase_anon_key, optional service_role
    │   └── supabase_clients.py   # get_supabase_anon(), get_supabase_admin() (lazy; admin needs service role)
    ├── api/
    │   ├── main.py               # FastAPI app factory, CORS, router mounts
    │   ├── dependencies.py       # get_db, get_current_user, service factories (DI)
    │   ├── exceptions.py         # HTTP exception handlers (standardized ErrorResponse)
    │   ├── schemas/              # Pydantic DTOs for API request/response
    │   │   ├── common.py         # ApiResponse, PaginatedResponse, ErrorResponse
    │   │   ├── hr/               # EmployeePublic, StaffAccountPublic, AttendanceLogInput/Output
    │   │   ├── crm/              # StudentPublic, ParentPublic, etc.
    │   │   ├── academics/        # CoursePublic, GroupPublic, SessionPublic
    │   │   ├── finance/          # ReceiptPublic, FinancialSummaryPublic
    │   │   └── analytics/          # DashboardSummaryPublic
    │   └── routers/
    │       ├── auth.py           # GET /me (Bearer JWT)
    │       ├── analytics/        # Split package: academic, financial, competition, bi
    │       │   ├── __init__.py   # Exports all sub-routers
    │       │   ├── academic.py   # Dashboard, unpaid attendees, roster, heatmap
    │       │   ├── financial.py  # Revenue by date/method, outstanding, top debtors
    │       │   ├── competition.py # Fee summary
    │       │   └── bi.py         # Trends, retention, performance, funnel, risk
    │       ├── academics/        # Split package: courses, groups, sessions
    │       │   ├── __init__.py
    │       │   ├── courses.py    # Course CRUD
    │       │   ├── groups.py     # Group CRUD + sessions by group
    │       │   └── sessions.py   # Session management
    │       ├── crm/              # Split package: students, parents
    │       │   ├── __init__.py
    │       │   ├── students.py   # Student CRUD + search + parents
    │       │   └── parents.py    # Parent CRUD + search
    │       ├── attendance_router.py
    │       ├── enrollments_router.py
    │       ├── finance_router.py
    │       ├── competitions_router.py
    │       └── hr_router.py      # Employee CRUD + staff accounts + attendance stub
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
    │   ├── constants.py          # MIN_PASSWORD_LENGTH, domain literals (e.g. EmploymentType)
    │   ├── datetime_utils.py     # utc_now, utc_now_iso, date_at_utc_midnight (UTC consistency)
    │   ├── audit_utils.py        # apply_create_audit / apply_update_audit (D4 created_at / updated_at / created_by)
    │   ├── validators.py
    │   └── exceptions.py         # NotFoundError, ValidationError, ConflictError, AuthError
    └── ui/
        ├── main.py               # Sidebar page_link entries + auth guard
        ├── state.py              # Session state helpers; `get_current_user_id()` → local `users.id` for audit columns
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

### 3.2 Schema Overview (30 tables — 16 core + 14 history/tracking)

| Table | Purpose | Key Constraints |
|---|---|---|
**Core Tables (16):**
| Table | Purpose | Key Constraints |
|---|---|---|
| `attendance` | Attendance per session | `UNIQUE(student_id, session_id)`; 7 columns |
| `competition_categories` | Categories within a competition | `ON DELETE CASCADE` from competition; 4 columns |
| `competitions` | Competition events | 8 columns |
| `courses` | Course catalog | `category IN ('software','hardware','steam','other')`; 10 columns |
| `employees` | Staff (instructors, admin) | `national_id` UNIQUE NOT NULL; `phone` NOT NULL UNIQUE; 17 columns |
| `enrollments` | Student enrolled in a group level | Partial UNIQUE: one active enrollment per (student, group); 14 columns |
| `groups` | Scheduling groups per course | `level_number` tracks current level; 15 columns |
| `parents` | Parent/parent contact records | phone_primary indexed; 9 columns |
| `payments` | Payment line items | `transaction_type IN ('charge','payment','refund')`; 11 columns |
| `receipts` | Payment receipt header | `payment_method IN ('cash','card','transfer','online')`; 14 columns |
| `sessions` | Individual class sessions | `session_date` DATE, `created_at` TIMESTAMPTZ; 14 columns |
| `student_parents` | M:M student–parent with primary flag | `UNIQUE(student_id, parent_id)`; 5 columns |
| `students` | Student profiles | `is_active` flag; `status` enum (active/waiting/inactive); 16 columns |
| `team_members` | Students in teams | `UNIQUE(team_id, student_id)`; `fee_paid BOOLEAN`; 5 columns |
| `teams` | Team per category | `enrollment_fee_per_student` can be NULL or float > 0; 11 columns |
| `users` | Login accounts | roles: `admin`, `system_admin`; `supabase_uid` UNIQUE NOT NULL; 8 columns |

**History & Tracking Tables (14):**
| Table | Purpose | Columns |
|---|---|---|
| `enrollment_balance_history` | Historical balance changes per enrollment | 10 |
| `enrollment_level_history` | Level progression tracking | 10 |
| `generated_receipts` | Generated receipt records | 11 |
| `group_competition_participation` | Group-competition linkage | 12 |
| `group_course_history` | Course assignment history for groups | 9 |
| `group_levels` | Group level progression management | 14 |
| `payment_allocations` | Payment distribution across enrollments | 10 |
| `receipt_templates` | Configurable receipt templates | 13 |
| `student_activity_log` | Audit trail of all student actions | 10 |
| `student_balances` | Current balance snapshot per student | 7 |
| `student_competition_history` | Competition participation records | 14 |
| `student_credits` | Credit balance tracking | 10 |
| `student_enrollment_history` | Enrollment lifecycle history | 15 |
| `student_payment_history` | Payment transaction history per student | 20 |

### 3.3 Views (12)

| View | Columns | What it gives you |
|---|---|---|
| `v_students` | 13 | students + primary parent name/phone joined |
| `v_enrollment_balance` | 9 | enrollment_id + `net_due`, `total_paid`, balance (live, computed from payments) |
| `v_enrollment_attendance` | 3 | enrollment_id + `sessions_attended`, `sessions_missed` |
| `v_siblings` | 5 | pairs of students who share a parent |
| `v_group_session_count` | 5 | group_id + level → `regular_sessions`, `extra_sessions`, `total_sessions` |
| `v_course_stats` | 6 | Course-level statistics |
| `v_daily_collections` | 7 | Daily payment collections summary |
| `v_payment_allocations_detailed` | 17 | Detailed payment allocation view |
| `v_student_activity_timeline` | 13 | Chronological student activity |
| `v_student_financial_summary` | 13 | Student financial overview |
| `v_student_payment_history` | 26 | Payment history with details |
| `v_unpaid_enrollments` | 16 | Unpaid enrollment listing |

> **Critical:** `v_enrollment_balance.balance` is a PostgreSQL `Decimal` — always cast to `float()` in Python before arithmetic.

### 3.4 `users` table and Supabase (v3.4)

- **`db/schema.sql` v3.4** defines `users` with **`supabase_uid`** (no `password_hash`) and role **`CHECK (admin, system_admin)`**.
- **Simplified roles (April 2026):** Reduced from 4 roles to 2 roles (`admin`, `system_admin`). All API operations now require `admin` or `system_admin` role.
- **API Guards:** `require_admin` (allows admin + system_admin), `require_any` (any authenticated user)
- **Canonical roles in code:** `app/modules/auth/constants.py` (`UserRole`, `ALL_ROLE_VALUES`, `is_valid_role`)
- **Upgrading old databases:** Migrate any `instructor`, `receptionist`, or `manager` roles to `admin` before deploying.
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

### 3.6 Audit timestamps (Sprint 3 / D4)

- **App:** `apply_create_audit` / `apply_update_audit` in `app/shared/audit_utils.py`; used by CRM, enrollment repo, academics `update_course` / `update_group` / `update_session`, etc.
- **DB:** Run `db/migrations/005_audit_d4_timestamps.sql` on existing databases after 004 (see `db/migrations/README.md`). If a statement fails inside the script’s `BEGIN` … `COMMIT`, run **`ROLLBACK;`** (or a new connection) before re-running the **entire** file — otherwise SQLSTATE **25P02**.
- **Greenfield:** `db/schema.sql` includes matching `DEFAULT CURRENT_TIMESTAMP` and `tf_set_updated_at` triggers on core tables.

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
- **Competitions:** Deep-SOLID architecture utilizing explicit directories for `models/`, `repositories/`, `services/`, and `schemas/` instead of single monolithic files. The facade `__init__.py` exposes singleton service methods.
- **API DTOs:** several modules expose `*_schemas.py` (Create/Read shapes) for FastAPI — alongside `*_models.py`.
- **`app/shared/base_repository.py`:** `RepositoryProtocol` for structural typing; repos may expose module-level aliases (e.g. `get_by_id`) without class inheritance.

The UI imports **only from `service.py`**, not from `repository.py`.

---

## 5. Module Reference

### 5.1 `app/modules/auth` (Supabase)

**Models (`auth_models.py`):** `User` (table), `UserBase`, `UserCreate` (optional `supabase_uid` until after Supabase signup), `UserRead`, **`UserPublic`** (no `supabase_uid` — use for JSON APIs).

**Roles:** `constants.py` — `UserRole` enum (`admin`, `system_admin`) / `is_valid_role`; `UserBase.role` validated against `ALL_ROLE_VALUES`.

**`auth_repository.py`:** `get_user_by_username`, `get_user_by_supabase_uid`, `get_users_by_employee_id`, `get_user_by_id`, `create_user`, `update_last_login`, `update_user`, …

**`auth_service.py`:** `get_user_by_supabase_uid`, `get_user_by_username`, `update_last_login` (commits after repo touch), `get_users_for_employee`, `force_reset_password` (Supabase admin), `link_employee_to_new_user` (Supabase admin + local `User` row).

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

### 5.2 `app/modules/crm` — Students & Parents

> **Naming:** DB/model = `parents` / `Parent`. UI text = "Parent". Python APIs keep `parent` in function names.

**Models:** `Parent`, `Student`, `StudentParent` (`crm_models.py`)

**repository.py:** `create_parent`, `get_parent_by_id`, `get_parent_by_phone`, `search_parents`, `create_student`, `get_student_by_id`, `search_students`, `get_student_parents`, `link_parent`, `get_siblings`, …

**service.py:** `validate_phone`, `register_parent`, `find_or_create_parent`, `search_parents`, `register_student`, `search_students`, `find_siblings`, `get_parent_students`, …

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
**Auto receipt_number format:** `TK-{year}-{id:05d}` (assigned in `finance_repository.set_receipt_number`)

**service.py:** `create_receipt_with_charge_lines` (single transaction — Financial Desk + competition fee), `open_receipt`, `add_charge_line`, `finalize_receipt`, `issue_refund`, `get_receipt_detail`, `get_daily_receipts`, **`search_receipts`** (date range on **`paid_at`**, optional parent / student / receipt #), `get_student_financial_summary`, `get_daily_collections`, `get_enrollment_balance`, …

**Dashboard (Sprint 4):** **`dashboard_receipts.render_receipt_browser`** on **`0_Dashboard.py`** → Financial Desk sub-tab; DB index **`idx_receipts_paid_at`** (`006` + **`schema.sql`**).

**Balance (P6 / B8):** View **`v_enrollment_balance.balance`** = **`total_paid − net_due`** — **negative** = debt, **zero** = settled, **positive** = credit. Migration **`007_p6_enrollment_balance.sql`**; analytics and Financial Desk use **debt** predicates (**`balance < 0`**). **Next:** [planning/sprint_6b_financial_desk_implementation_plan.md](planning/sprint_6b_financial_desk_implementation_plan.md) (U2, U9, B3, P8 phase A).

---

### 5.7 `app/modules/competitions`

**Architecture:** Deep-SOLID Refactored. The module uses separated directories natively: `models/`, `schemas/`, `repositories/`, `services/`.
**Models:** `Competition`, `CompetitionCategory` (in `models/competition_models.py`); `Team`, `TeamMember` (in `models/team_models.py`).
**Hierarchy:** Competition → Category → Team → TeamMember
**DTOs:** Uses strict Pydantic typed objects for input commands and output views (e.g., `TeamMemberRosterDTO`, `CompetitionSummaryDTO`).

**Services:**

- **`CompetitionService`**: `create_competition`, `list_competitions`, `update_competition`, `delete_competition`, category CRUD, `get_competition_summary`.
- **`TeamService`**: `get_student_competitions`, `register_team`, `list_teams`, `update_team`, `delete_team`, `add_team_member_to_existing`, `remove_team_member`, `list_team_members`, `pay_competition_fee`, `unmark_team_fee_for_payment`.

**Facade:** `app/modules/competitions/__init__.py` globally instantiates these singletons and maps their methods for UI backward compatibility.

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
| `nav_target_parent_id` | Parent/parent detail (Directory) |
| `nav_target_group_id` | Group-focused flows (legacy naming; some pages use `selected_group_id` from Dashboard) |
| `nav_target_course_id` | Course detail |
| `selected_receipt_id` | Finance receipt detail inside Dashboard tab |
| `dash_rcpt_last_search` | Last receipt browser query params (Browse receipts tab) |
| `user` | Auth session — set after successful login |
| `access_token` | Supabase JWT — stored for future API calls |

### 6.3 Pages (actual filenames)

| File | Role | How reached |
|---|---|---|
| `0_Dashboard.py` | KPIs, today's sessions → group navigation, **Financial Desk** tab (**Browse receipts** / **Record payment** + receipt detail), **Quick Registration** | Sidebar |
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
| Finance | `finance_overview.py`, `finance_receipt.py`, `dashboard_receipts.py` |
| Competitions | `competition_overview.py`, `competition_detail.py` |
| Staff | `employee/employee_directory.py`, `employee_detail.py`, `employee_form.py` — use `hr_service` + `auth_service` (`get_users_for_employee`, `create_staff_account`, `update_staff_account`, `force_reset_password`, `link_employee_to_new_user`); roles from `UserRole` |
| Dashboard | `quick_register.py` |
| Reports | `charts/*.py` (e.g. retention, utilization, instructor matrix) |
| Forms | `forms/edit_*.py` |

---

## 7. FastAPI snapshot (`app/api/`)

- **`create_app()`** in `main.py` — title *Techno Terminal  API*, **CORS open** (`allow_origins=["*"]`) for development.
- **Routers:** `auth` mounted at `/api/v1/auth` — **`GET /api/v1/auth/me`** — `Authorization: Bearer <supabase_jwt>` — response **`UserPublic`**.
- **`GET /health`** — liveness check.
- **`get_db`** — yields a `Session` scoped to the request (uses `get_session()` context manager pattern).
- **Exception handlers:** `app/api/exceptions.py`

**Phase 5 status:** **COMPLETE** — All routers implemented (15 total): auth, CRM (students/parents/history), academics (courses/groups/sessions/lifecycle/competitions), enrollments, attendance, finance (balance/receipts/finance), competitions, HR, analytics (academic/financial/competition/BI). See `app/api/main.py` for full router registration.

---

## 8. Architectural Decision Records

| # | Decision | Rationale |
|---|---|---|
| ADR-1 | Streamlit as primary internal UI; FastAPI API added for scale / future clients | Internal ops stay simple; JSON API for mobile/web clients without duplicating business logic |
| ADR-2 | SQLModel (not raw SQLAlchemy only) | Pydantic validation + SQLAlchemy in one |
| ADR-3 | `get_session()` as context manager | Auto-commit on exit, rollback on exception; `expire_on_commit=False` |
| ADR-4 | `enrollment.level_number` is a snapshot | Historical enrollments stay stable when group advances |
| ADR-5 | `student_parents` junction | M:M parents; sibling detection via `v_siblings` |
| ADR-6 | Receipts + Payment lines | One receipt, many students; refunds as new rows |
| ADR-7 | NULL/zero-fee teams auto-mark paid | Academy-sponsored teams |
| ADR-8 | Parent (code) vs Parent (UI) | Avoid breaking imports; consistent UX wording |
| ADR-9 | Analytics raw SQL (`text()`) | Aggregations and window functions stay readable |
| ADR-10 | Supabase for identity | Centralized auth; local `users.supabase_uid` mapping |
| ADR-11 | Canonical `UserRole` in code + DB CHECK | Single extensibility path for roles (`role_types.py` + migrations) |
| ADR-12 | Hybrid DB workflow | `db/schema.sql` for full DDL; `db/migrations/*.sql` for ops upgrades; Alembic for revision tracking |

---

## 9. Standard Workflows

### Finance Flow

```
Preferred (one commit): create_receipt_with_charge_lines(parent_id, method, user_id, lines) -> dict summary + payment_ids

Legacy / granular:
1. open_receipt(parent_id, method, user_id)        -> Receipt
2. add_charge_line(receipt_id, student_id, ...)      -> Payment (repeat per student)
3. finalize_receipt(receipt_id)                      -> dict summary
4. (Competition) pay_competition_fee(...)            -> receipt + mark_fee_paid
5. (Refund) issue_refund(payment_id, ...)            -> new receipt + refund line
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
3. **`search_Parents` / `list_groups` do NOT exist** — use `search_parents`, `get_all_active_groups()`, etc.
4. **Session state navigation** — prefer `.pop("nav_key")` when consuming one-shot navigation ids.
5. **`st.switch_page()` path** — must match the filename under `pages/` (e.g. `"pages/1_Directory.py"`, `"pages/0_Dashboard.py"`).
6. **`expire_on_commit=False`** — objects stay usable after close; do not share across threads.
7. **Zero-fee teams** — `enrollment_fee_per_student is None or == 0` → treat as paid where applicable.
8. **`CourseSession` location** — `academics_session_models.py`, not `academics_models.py`.
9. **`session` parameter name** — in repos, `session` is the **SQLModel DB session**, not HTTP session.
10. **Analytics DataFrames** — rename columns by **name**, not by positional index.
11. **`db/schema.sql` v3.3** — `users` matches ORM for Supabase auth; use `db/migrations/` for older DBs (§3.4).
12. **Refactoring backlog doc** — `docs/memory_bank/05_reviews/refactoring_backlog.md` predates the populated `app/api/` tree; use this MEMORY_BANK + code for current layout.
13. **Failed SQL migration in a transaction** — after any error in a `BEGIN` … `COMMIT` script (e.g. `005_audit_d4_timestamps.sql`), run **`ROLLBACK;`** or use a fresh session; partial re-runs yield **25P02** until then (see header in that file and `db/migrations/README.md`).

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
# psql $DATABASE_URL -f db/migrations/005_audit_d4_timestamps.sql   # D4 audit defaults + triggers (after 003/004 as ordered)

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
| 1 | DB schema, student/parent CRUD |
| 2 | Course catalog, groups, session generation |
| 3 | Enrollment with level snapshots |
| 4 | Finance: receipts, payments, balances |
| 5 | Competitions; parent profile competition fees |
| 5 Polish | Competition inline edit/delete; Parent UI wording; wide layout |
| 6 | Analytics; Dashboard; Reports tabs; exports |
| 7 | FastAPI scaffold, Supabase JWT deps, `run_api`, auth `/me`, HR + staff UI, Directory consolidation |
| 8 | Auth hardening: `UserRole`, `UserPublic`, `HTTPBearer`, lazy Supabase clients; schema v3.3; JSONB metadata on models; `db/migrations/002`, Alembic baseline; employee UI wired to services |
| 9 | Sprint 3 (D4): `audit_utils`, migration `005` + schema audit defaults/triggers; CRM/enrollment/UI actor threading; `CourseSession` DATE/TIMESTAMPTZ ORM alignment; academics update DTOs + `apply_update_audit`; `state.get_current_user_id()` |
| 10 | **API Code Review Fixes:** Router splitting (analytics/academics/crm), 14 new analytics endpoints, HR CRUD endpoints, DTO-ification, standardized DI patterns, HTTPException handler |
| 11 | **API Finalization (2026-04-02):** Auth endpoints (login/logout/refresh/users), Sessions daily-schedule, Competition CRUD, Finance PDF export, role simplification to admin/system_admin. Backend 100% ready. |

**Completed plan write-ups:** `docs/archive/legacy_plans/` ([README](archive/legacy_plans/README.md)) — memory-bank refresh summary, auth/DB alignment task list.

**Active planning (product + API rollout):**

- `docs/planning/qa_backlog_2026_03_testing_findings.md` — QA findings, story points, product decisions **P1–P9**
- `docs/planning/sprint_roadmap_post_qa_2026.md` — ordered product/engineering sprints after QA
- `docs/planning/phase5_api_execution_roadmap_2026.md` — Phase 5.1–5.5 API delivery plan

**See also (longer-form, may predate code):**

- `docs/archive/legacy_plans/` — archived summaries of completed engineering plans  
- `docs/memory_bank/01_business_domain/` — requirements, data dictionary, project origin  
- `docs/memory_bank/02_database_design/` — schema narrative  
- `docs/memory_bank/03_etl_pipeline/` — **historical** Excel ETL context (no `src/` pipeline in this repo snapshot)  
- `docs/memory_bank/04_architecture/` — phased technical plans, session management, API plan  
- `docs/memory_bank/05_reviews/` — architecture / SaaS reviews, refactoring backlog  

---

## 13. Documentation drift policy

When the repo and `docs/memory_bank/*` disagree, **treat this `MEMORY_BANK.md` and the code as authoritative** for agents; use subdocs for background and intent, then verify against `app/` and `db/`.

---

## 14. Frontend Development (Active — Next Session)

**Status:** Backend complete. Frontend not yet started.  
**Plan document:** [`docs/planning/FRONTEND_PLAN.md`](planning/FRONTEND_PLAN.md)  
**Product spec:** [`docs/product/frontend_handover.md`](product/frontend_handover.md)

### Agreed Stack
| Layer | Choice |
|-------|--------|
| Framework | **Vite + React 18 + TypeScript** |
| Routing | React Router v6 |
| Server State | TanStack Query (React Query) |
| Auth/Global State | Zustand (persisted to localStorage) |
| HTTP | Axios with JWT interceptor |
| Styling | Vanilla CSS + CSS Variables (dark theme) |

### MVP Phase Order
| Phase | Deliverable | API Ready |
|:-----:|-------------|:---------:|
| 0 | Scaffold + Axios client + Auth store + Layout | ✅ |
| 1 | Login page | ✅ |
| 2 | Dashboard (daily schedule + attendance grid) | ✅ |
| 3 | Group Detail + Attendance Grid component | ✅ |
| 4 | Directory (Students + Parents + detail views) | ✅ |
| 5 | Enrollments page | ✅ |
| 6 | Finance & Receipts page | ✅ |

### Key Architecture Notes for Frontend Agent
- **Auth Flow:** `POST /api/v1/auth/login` → store `access_token` in Zustand. Axios interceptor auto-injects `Authorization: Bearer <token>`. On 401 → logout + redirect to `/login`.
- **Daily Schedule:** `GET /api/v1/academics/sessions/daily-schedule?day=Saturday` — day name (English, e.g. `Saturday`) not a date.
- **Attendance Grid:** Must use local in-memory state map. **No API call per cell click.** Only fire on "Save All" button — one `POST` per session column with changes.
- **Balance badges:** Fetch `GET /finance/balance/student/{id}` to show 🟢/🔴 debt status on attendance grid rows.
- **PDF download:** `GET /finance/receipts/{id}/pdf` returns `application/pdf` with `Content-Disposition: attachment`.
- **CORS:** Backend configured for `localhost:5173` (Vite default). Use Vite proxy in dev.
- **Role check:** Only 2 roles: `admin`, `system_admin`. All pages require auth. No instructor/receptionist routes exist.
