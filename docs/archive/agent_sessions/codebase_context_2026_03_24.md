# Techno Terminal — Full Codebase Context
> **Generated:** 2026-03-24  
> **Branch:** `feature/api-layer`  
> **Last committed sprint:** Sprint 6b (`12fd3db`)  
> **Schema version:** v3.3 (15 tables, 5 views)  
> **Stack:** Streamlit + FastAPI + SQLModel + PostgreSQL + Supabase Auth

---

## 1. What This Project Is

**Techno Terminal** is a full-stack internal management system for a STEM education center. It manages:

- Student & parent (parent) profiles
- Course catalog, group scheduling, session tracking
- Student enrollment per group/level
- Attendance marking
- Financial receipts, payments, discounts, refunds
- Competition registration (teams, categories, fees)
- Analytics and reporting dashboards
- Staff directory + linked login accounts

**Two transport layers (same services):**
- **Streamlit** (`app/ui/`) — primary internal UI. Pages call service functions directly in-process.
- **FastAPI** (`app/api/`) — REST API for future clients. Phase 5.1 scaffold is live; domain routers are NOT mounted yet.

---

## 2. Repo Structure

```
project_root/
├── run_ui.py                     # Entry — seeds admin (Supabase), starts Streamlit on app/ui/main.py
├── run_api.py                    # Uvicorn for FastAPI (port 8000, --reload)
├── .env                          # DATABASE_URL, SUPABASE_* (not committed)
├── .env.example
├── pyproject.toml
├── requirements.txt
├── alembic.ini / alembic/        # Revision tracking; 001_baseline_v33 = schema.sql baseline
├── db/
│   ├── schema.sql                # CANONICAL full DDL v3.3 (greenfield installs only)
│   └── migrations/
│       ├── README.md             # Apply order + 25P02 recovery note
│       ├── supabase_auth_patch.sql       # Legacy: password_hash → supabase_uid
│       ├── 002_users_supabase_roles_v33.sql
│       ├── 003_employees_employment_full_time.sql
│       ├── 004_employees_sprint2_identity.sql   # national_id, education, uniqueness
│       ├── 005_audit_d4_timestamps.sql          # D4 audit backfill + triggers
│       ├── 006_receipts_paid_at_index.sql       # idx_receipts_paid_at (Sprint 4)
│       └── 007_p6_enrollment_balance.sql        # P6 sign-flip on v_enrollment_balance
├── docs/
│   ├── MEMORY_BANK.md            # Primary handoff reference (authoritative over subdocs)
│   └── reviews/
│       ├── qa_backlog_2026_03_testing_findings.md
│       ├── sprint_roadmap_post_qa_2026.md        # v1.7
│       ├── sprint_5_b8_balance_design_spike.md
│       ├── sprint_6b_financial_desk_implementation_plan.md
│       └── phase5_api_execution_roadmap_2026.md
└── app/
    ├── core/
    │   ├── config.py             # Pydantic Settings (DATABASE_URL, SUPABASE_*)
    │   └── supabase_clients.py   # get_supabase_anon(), get_supabase_admin() (lazy)
    ├── api/
    │   ├── main.py               # FastAPI app factory, CORS open (*), router mounts
    │   ├── dependencies.py       # get_db, get_current_user (HTTPBearer → Supabase JWT)
    │   ├── exceptions.py
    │   └── routers/auth.py       # GET /api/v1/auth/me → UserPublic
    ├── db/
    │   ├── connection.py         # get_engine() + get_session() context manager
    │   ├── seed.py               # Supabase admin-linked seed row
    │   └── init_db.py            # ORM drop/create + views (RAW_VIEWS_SQL) + seed
    ├── modules/                  # Domain modules (models → repo → service)
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
    │   ├── constants.py
    │   ├── datetime_utils.py     # utc_now(), utc_now_iso(), date_at_utc_midnight()
    │   ├── audit_utils.py        # apply_create_audit() / apply_update_audit()
    │   ├── validators.py
    │   └── exceptions.py        # ConflictError, NotFoundError, etc.
    └── ui/
        ├── main.py               # Sidebar page_link + auth guard
        ├── state.py              # get_current_user_id() → local users.id
        ├── pages/                # 0_Dashboard, 1_Directory, 3_Course_Management,
        │                         # 4_Group_Management, 5_Enrollment, 6_Staff_Management,
        │                         # 8_Competitions, 9_Reports, login.py
        └── components/           # Reusable UI fragments (see §6)
```

---

## 3. Database Architecture

### 3.1 Connection Pattern (`app/db/connection.py`)

```python
get_engine()   # Lazy singleton, pool_size=5, max_overflow=5, pool_recycle=1800
get_session()  # @contextmanager — yields Session, auto-commits on exit, rolls back on exception
               # CRITICAL: expire_on_commit=False — objects stay accessible after close
```

### 3.2 Tables (15, dependency order)

| Table | Key Notes |
|-------|-----------|
| `parents` | Parent contacts; `phone_primary` indexed |
| `employees` | `national_id` NOT NULL UNIQUE; `phone` NOT NULL UNIQUE; `email` UNIQUE nullable; `employment_type` NOT NULL; D5 CHECK on `contract_percentage` |
| `users` | `supabase_uid` UNIQUE NOT NULL; roles: `admin`, `instructor`, `system_admin`; optional `employee_id` FK |
| `students` | `is_active` flag; no direct parent FK — uses junction |
| `student_parents` | M:M junction; `UNIQUE(student_id, parent_id)`; `is_primary` flag |
| `courses` | `category IN ('software','hardware','steam','other')` |
| `groups` | `level_number` = current active level; `status IN ('active','completed','cancelled')` |
| `sessions` | `session_date DATE`, `created_at TIMESTAMPTZ`; ORM uses `date`/`datetime` (not `str`); `ON DELETE RESTRICT` on `group_id` |
| `enrollments` | `level_number` = **snapshot** at enrollment time; partial UNIQUE: one active per (student, group); `status IN ('active','completed','transferred','dropped')` |
| `attendance` | `UNIQUE(student_id, session_id)`; `enrollment_id` NOT NULL; statuses: `present`, `absent`, `late`, `excused` (`unmarked` = virtual/UI only) |
| `receipts` | `payment_method IN ('cash','card','transfer','online')`; `receipt_number` format `TK-{year}-{id:05d}` |
| `payments` | `transaction_type IN ('charge','payment','refund')`; `amount != 0` |
| `competitions` | Event header |
| `competition_categories` | `ON DELETE CASCADE` from competition |
| `teams` | `enrollment_fee_per_student` nullable; NULL or 0 = auto-mark paid |
| `team_members` | `UNIQUE(team_id, student_id)`; `fee_paid BOOLEAN` |

### 3.3 Views (5)

| View | What It Gives |
|------|---------------|
| `v_students` | students + primary parent name/phone |
| `v_enrollment_balance` | `net_due`, `total_paid`, **`balance = total_paid − net_due`** (P6: **negative = debt**, zero = settled, **positive = credit**) |
| `v_enrollment_attendance` | `sessions_attended`, `sessions_missed` per enrollment |
| `v_siblings` | Student pairs sharing a parent |
| `v_group_session_count` | `regular_sessions`, `extra_sessions`, `total_sessions` per group/level |

> ⚠️ `v_enrollment_balance.balance` returns `Decimal` — always `float()` cast in Python before arithmetic.

### 3.4 JSONB `metadata` columns (Python name ≠ SQL name)

| SQL column | Python attribute | Module |
|------------|-----------------|--------|
| `employees.metadata` | `employee_metadata` | `hr_models` |
| `students.metadata` | `profile_metadata` | `crm_models` |
| `groups.metadata` | `group_metadata` | `academics_models` |
| `enrollments.metadata` | `enrollment_metadata` | `enrollment_models` |
| `payments.metadata` | `payment_metadata` | `finance_models` |
| `teams.metadata` | `team_metadata` | `competition_models` |

---

## 4. Module Architecture Pattern

Every domain module is **3-layer**:

```
*_models.py     SQLModel ORM classes (table=True)
*_repository.py Pure data access — accepts Session, returns ORM objects or dicts
*_service.py    Business logic — opens get_session() internally, calls repo, raises exceptions
```

**Rule:** UI imports **only from `service.py`**, never from `repository.py`.

**DTOs:** modules that expose FastAPI endpoints also have `*_schemas.py` with Pydantic request/response shapes.

---

## 5. Domain Modules Reference

### 5.1 `auth`
- `auth_models.py` — `User`, `UserBase`, `UserCreate`, `UserRead`, **`UserPublic`** (no `supabase_uid` — use for APIs)
- `role_types.py` — `UserRole` enum, `is_valid_role()`, `ALL_ROLE_VALUES`
- `auth_repository.py` — `get_user_by_username`, `get_user_by_supabase_uid`, `create_user`, `update_last_login`, `update_user`, …
- `auth_service.py` — `update_last_login` (explicit `session.commit()` post-repo; `get_session()` also commits); `link_employee_to_new_user`, `force_reset_password`
- API: `GET /api/v1/auth/me` → `UserPublic`; auth via `HTTPBearer` (raw Supabase JWT, NOT OAuth2 password flow)

### 5.2 `hr`
- `hr_models.py` — `Employee`, `EmployeeBase`, `EmployeeCreate` (strip validators, national_id ≥10 chars), `EmployeeRead`
- `hr_repository.py` — `EMPLOYEE_FIELD_KEYS`, `find_employee_by_national_id/phone/email`, create/update gated to allowed keys
- `hr_service.py` — duplicate checks → `ConflictError`; `IntegrityError` → friendly message; `update_employee_only` merges with DB row (doesn't wipe `monthly_salary`)
- UI: `employee_directory.py`, `employee_detail.py`, `employee_form.py` (busy flags for double-submit guard)

### 5.3 `crm`
- **Naming:** DB/code = `parent`; UI text = "Parent"
- Models: `Parent`, `Student`, `StudentParent` in `crm_models.py`
- Repository: `create_parent`, `get_parent_by_phone`, `search_parents`, `create_student`, `search_students`, `link_parent`, `get_siblings`, …
- Service: `register_parent`, `find_or_create_parent`, `register_student`, `search_students`, `find_siblings`, `get_parent_students`, …
- Audit: create paths use `apply_create_audit()`; update paths use `apply_update_audit()`

### 5.4 `academics`
- Models: `Course`, `Group` in `academics_models.py`; **`CourseSession` in `academics_session_models.py`** (separate file — avoid circular imports)
- **`Group.level_number`** = current active level (NOT `current_level`)
- Time constraint: groups scheduled between **11:00 AM – 9:00 PM**
- Key service functions: `add_new_course`, `schedule_group`, `generate_level_sessions`, `advance_group_level`, `get_all_active_groups_enriched`, `check_level_complete`, …
- DTOs in `academics_schemas.py`: `UpdateCourseDTO`, `UpdateGroupDTO`, `UpdateSessionDTO`
- `update_course` / `update_group` / `update_session` all call `apply_update_audit()` before commit

### 5.5 `enrollments`
- Model: `Enrollment` — `level_number` is a **snapshot** of group's level at enrollment time (historical stability)
- Service: `enroll_student`, `get_student_enrollments`, `get_group_enrollments`, `transfer_enrollment`, `drop_enrollment`

### 5.6 `attendance`
- Valid DB statuses: `present`, `absent`, `late`, `excused`
- `unmarked` = **virtual** UI label when no attendance row exists

### 5.7 `finance` ⚡ Most-active module
- Models: `Receipt`, `Payment`
- **Preferred flow (one atomic transaction):**
  ```python
  create_receipt_with_charge_lines(parent_id, method, user_id, lines, allow_credit=True) → dict summary + payment_ids
  ```
- **Legacy/granular flow:** `open_receipt` → `add_charge_line` (loop) → `finalize_receipt`
- Other service functions: `issue_refund`, `search_receipts` (UTC half-open on `paid_at`, LIMIT 200), `get_enrollment_balance`, `preview_overpayment_risk(lines, db=...)`, `get_daily_receipts`, `get_student_financial_summary`
- **P6 balance convention:** `balance = total_paid - net_due` → `balance < 0` = debt, `balance > 0` = credit
- `__init__.py` exports: `create_receipt_with_charge_lines`, `ReceiptLineInput`, `preview_overpayment_risk`, `search_receipts`

### 5.8 `competitions`
- Hierarchy: `Competition → CompetitionCategory → Team → TeamMember`
- `enrollment_fee_per_student = NULL or 0` → auto-mark fee paid
- Service: `create_competition`, `list_competitions`, `add_member_to_team`, `mark_team_fee_paid`, `remove_member_from_team`, …

### 5.9 `analytics`
- All return `list[dict]` or scalars; always `float()` cast monetary columns
- Raw SQL via `text()` — `get_today_unpaid_attendees`, `get_outstanding_by_group`, `get_top_debtors`, `get_revenue_by_date`, `get_attendance_heatmap`, `get_instructor_value_matrix`, `get_flight_risk_students`, `get_competition_fee_summary`, …
- All analytics P6-aligned: debt predicates use `balance < 0`

---

## 6. UI Architecture

### 6.1 Pages

| File | Role |
|------|------|
| `0_Dashboard.py` | KPIs, today's sessions, **Financial Desk** (tabs: Browse receipts / Record payment), **Quick Registration** |
| `1_Directory.py` | Tabs: Parents / Students; detail views via `nav_target_*` keys |
| `3_Course_Management.py` | Courses |
| `4_Group_Management.py` | Groups, sessions, attendance |
| `5_Enrollment.py` | Enrollment / transfers (passes `created_by` for audit) |
| `6_Staff_Management.py` | Staff directory + add employee |
| `8_Competitions.py` | Competitions |
| `9_Reports.py` | Multi-tab reports + heatmaps |
| `login.py` | Supabase login; sets `user` + `access_token` in session state |

### 6.2 Session State Navigation Pattern

```python
# Sender:
st.session_state["nav_target_student_id"] = student.id
st.switch_page("pages/1_Directory.py")

# Receiver:
if "nav_target_student_id" in st.session_state:
    render_student_detail(st.session_state.pop("nav_target_student_id"))
```

**Active session keys:**

| Key | Purpose |
|-----|---------|
| `nav_target_student_id` | Student detail cross-link |
| `nav_target_parent_id` | Parent detail cross-link |
| `nav_target_group_id` | Group detail |
| `nav_target_course_id` | Course detail |
| `selected_receipt_id` | Receipt detail in Dashboard tab |
| `dash_rcpt_last_search` | Last receipt browser search params |
| `user` | Auth session object |
| `access_token` | Supabase JWT for API calls |

### 6.3 Key Components

| Component | File | Role |
|-----------|------|------|
| Finance Desk | `finance_overview.py` | Student/parent search, owed-only toggle, household balance, overpayment warn+confirm, record payment |
| Receipt Browser | `dashboard_receipts.py` | Date-range search, row select → detail |
| Receipt Detail | `finance_receipt.py` | Reusable receipt detail + refund |
| Quick Register | `quick_register.py` | New student + parent from Dashboard |
| Auth guard | `auth_guard.py` | `require_auth()` wrapper |
| Employee forms | `employee/employee_form.py`, `employee_directory.py`, `employee_detail.py` |

---

## 7. FastAPI Status

- **Phase 5.1 LIVE:** `GET /api/v1/auth/me`, `GET /health`, global exception handlers, `get_db`
- **Auth:** `HTTPBearer` — raw Supabase JWT (NOT `/token` endpoint)
- **CORS:** open `*` (development)
- **Phase 5.2–5.5 (domain routers): NOT yet mounted** — commented placeholders in `main.py`
- **Roadmap:** `docs/reviews/phase5_api_execution_roadmap_2026.md`

---

## 8. Shared Utilities

| File | Exports |
|------|---------|
| `audit_utils.py` | `apply_create_audit(obj, created_by=None)` — stamps `created_at` + optional `created_by`; `apply_update_audit(obj)` — bumps `updated_at` |
| `datetime_utils.py` | `utc_now()`, `utc_now_iso()`, `date_at_utc_midnight()` |
| `exceptions.py` | `ConflictError`, `NotFoundError`, `ValidationError` (app-level) |
| `constants.py` | `MIN_PASSWORD_LENGTH`, `EmploymentType` literals |
| `state.py` (ui) | `get_current_user_id()` → local `users.id` for audit columns (`created_by`, `received_by`) |

---

## 9. Authentication Flow

```
Login (Streamlit) → supabase.sign_in_with_password()
  → stores user + access_token in st.session_state
  → update_last_login() → auth_service explicit commit + get_session() auto-commit

API calls (FastAPI) → Authorization: Bearer <supabase_jwt>
  → get_current_user() in dependencies.py
  → supabase.auth.get_user(token)
  → get_user_by_supabase_uid() → local User
  → 403 if is_active = False
```

---

## 10. Sprint History & Current State

| Sprint | Focus | Commit | Status |
|--------|-------|--------|--------|
| 1 | Receipt # integrity — atomic `create_receipt_with_charge_lines` | — | ✅ Done |
| 2 | HR identity, constraints, migration 004 | — | ✅ Done |
| 3 | Audit D4 — `audit_utils`, migration 005, triggers | `1b803f1` | ✅ Done |
| 4 | Dashboard receipt browser — `search_receipts`, migration 006 | `8e17786` | ✅ Done |
| 5 | Balance design spike — `sprint_5_b8_balance_design_spike.md` | — | ✅ Done (doc) |
| 6 | P6 balance flip — `balance = total_paid - net_due`, migration 007 | `3bf1ed6` | ✅ Done |
| **6b** | **Financial Desk completion — student search, owed-only, overpay confirm** | **`12fd3db`** | **✅ Done** |

### Sprint 6b — What Was Implemented (Latest)

- **`finance_overview.py`:** Student search entry path; auto-resolves to parent; "Show owed money only" toggle (P7); household balance rollup (P5/P6)
- **`finance_service.py`:** `create_receipt_with_charge_lines(..., allow_credit: bool = True)` guard; `preview_overpayment_risk(lines, db=...)` helper — pre-flight scan before receipt creation
- **`finance/__init__.py`:** Exports `preview_overpayment_risk`

---

## 11. What's Open / Next Steps

### Immediately Open

| Item | Status |
|------|--------|
| **P8 Phase B** — auto-apply credit across future enrollments | Design needed; Phase A (warn+confirm) is done |
| **Sprint 7** — Course aggregates (B5/D3/U5) — `get_course_stats` | Not started |
| **Phase 2** — PDF receipts (U6/B6) | Not started |
| **Phase 2** — Competition fee model (U7/B7) | Not started |
| **Phase 5.2–5.5** — FastAPI domain routers (CRM, academics, finance, analytics) | Planned, not started |
| **Supabase DB migration** — local PostgreSQL → Supabase | Steps in `db/README.md`; `users.supabase_uid` alignment needed |

### Last User Message (End of Cursor session)
> *"great — explain me what is the next move of our plan / what is our state from the sprints document we wrote"*

**Answer:** All sprints 1–6b are done. The roadmap's next moves are:
1. **Sprint 7** — Course aggregates
2. **P8 Phase B** — Credit auto-application design
3. **Phase 5 API** — Domain routers (CRM first per execution roadmap)
4. **Supabase cutover** — if not yet done

---

## 12. Critical Pitfalls (Don't Get These Wrong)

| # | Pitfall |
|---|---------|
| 1 | `v_enrollment_balance.balance` is `Decimal` — always `float()` before arithmetic |
| 2 | `group.current_level` **does NOT exist** — use `group.level_number` |
| 3 | `CourseSession` is in `academics_session_models.py`, NOT `academics_models.py` |
| 4 | `session` param in repos = **DB Session**, not HTTP session |
| 5 | `_EMPLOYEE_CREATE_KEYS` **is dead** — the constant is `EMPLOYEE_FIELD_KEYS` |
| 6 | `sessions.created_at` and `session_date` are `TIMESTAMPTZ`/`DATE` — never `str` |
| 7 | After a `BEGIN…COMMIT` migration fails, run **`ROLLBACK;`** before re-running (else SQLSTATE 25P02) |
| 8 | Zero-fee teams (`enrollment_fee_per_student IS NULL or = 0`) → auto-mark as paid |
| 9 | `expire_on_commit=False` — objects usable after session close; don't share across threads |
| 10 | `search_Parents` / `list_groups` **do not exist** — use `search_parents`, `get_all_active_groups()` |
| 11 | `st.switch_page()` path must match filename exactly under `pages/` |
| 12 | `update_course` / `update_group` / `update_session` all call `apply_update_audit()` before commit |
| 13 | `balance < 0` = debt (P6); `balance > 0` = credit — never invert this convention |

---

## 13. Environment & Dev Commands

```bash
# Run UI (seeds admin if SUPABASE_SERVICE_ROLE_KEY set)
python run_ui.py

# Run API
python run_api.py

# Apply specific migration on existing DB
psql "$DATABASE_URL" -f db/migrations/007_p6_enrollment_balance.sql

# Fresh greenfield DB
psql "$DATABASE_URL" -f db/schema.sql
alembic stamp 001_baseline_v33

# Windows venv activate
.venv\Scripts\activate
```

**Required env vars:**
- `DATABASE_URL` — PostgreSQL connection string
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — login + JWT verification  
- `SUPABASE_SERVICE_ROLE_KEY` — required for staff account creation, `force_reset_password`, admin seed

---

*Document is authoritative for agent handoff. If code and docs conflict, trust the code and this document over older subdocs in `docs/memory_bank/`.*
