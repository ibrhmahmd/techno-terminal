# Techno Kids CRM — Memory Bank
> **Purpose:** Complete architectural and code-level reference for AI agent handoff.  
> **Last updated:** 2026-03-18  
> **Schema version:** v3.2 (15 tables, 5 views)  
> **Framework:** Streamlit + SQLModel + PostgreSQL

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

The application is a **Streamlit multi-page app** backed by **PostgreSQL**. There is no REST API consumed by the frontend — all data access goes through the Python service/repository layer directly.

---

## 2. Repo Structure

```
project_root/
├── run_app.py                    # Entry point — seeds DB, launches Streamlit
├── .env                          # DATABASE_URL + secrets (not committed)
├── .env.example                  # Template for required env vars
├── pyproject.toml                # Project metadata & deps
├── requirements.txt              # Pinned dependencies
├── db/
│   └── schema.sql                # Single source of truth for DB schema (v3.2)
├── docs/
│   └── MEMORY_BANK.md            # THIS FILE
└── app/
    ├── __init__.py
    ├── db/
    │   ├── connection.py         # SQLModel engine + get_session() context manager
    │   └── seed.py               # Seeds admin user on first run
    ├── modules/                  # Business logic — layered (models → repo → service)
    │   ├── auth/
    │   ├── crm/
    │   ├── academics/
    │   ├── enrollments/
    │   ├── attendance/
    │   ├── finance/
    │   ├── competitions/
    │   └── analytics/
    └── ui/
        ├── main.py               # Sidebar layout + auth guard
        ├── state.py              # Session state helpers
        ├── pages/                # Streamlit numbered pages
        └── components/           # Reusable UI fragments
```

---

## 3. Database Architecture

### 3.1 Connection ([app/db/connection.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/db/connection.py))

```python
get_engine()      # Lazy singleton SQLAlchemy engine from DATABASE_URL
get_session()     # @contextmanager — yields Session, auto-commit on exit, rollback on exception
                  # CRITICAL: expire_on_commit=False so objects are usable after the session closes
```

**Connection pool config:** `pool_size=5`, `max_overflow=5`, `pool_timeout=30`, `pool_recycle=1800`

### 3.2 Schema Overview (15 tables, dependency order)

| Table | Purpose | Key Constraints |
|---|---|---|
| [guardians](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py#74-80) | Parent/guardian contact records | phone_primary indexed |
| [employees](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/repository.py#30-33) | Staff (instructors, admin) | `employment_type IN ('part_time','contract')` |
| `users` | Login accounts | roles: `admin`, `system_admin`; linked to [employees](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/auth/repository.py#30-33) |
| [students](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py#54-58) | Student profiles | `is_active` flag; no guardian FK — uses junction table |
| [student_guardians](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py#60-66) | M:M student-guardian with primary flag | `UNIQUE(student_id, guardian_id)` |
| [courses](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/service.py#81-84) | Course catalog | `category IN ('software','hardware','steam','other')` |
| [groups](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/repository.py#74-96) | Scheduling groups per course | `level_number` tracks current level; `status IN ('active','completed','cancelled')` |
| [sessions](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/repository.py#142-150) | Individual class sessions | `ON DELETE RESTRICT` on `group_id` — cannot delete group with sessions |
| [enrollments](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/repository.py#30-44) | Student enrolled in a group level | Partial UNIQUE index: one active enrollment per (student, group); `status IN ('active','completed','transferred','dropped')` |
| [attendance](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/attendance/repository.py#7-29) | Attendance per session | `UNIQUE(student_id, session_id)`; `enrollment_id` NOT NULL |
| [receipts](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/finance/service.py#161-167) | Payment receipt header | `payment_method IN ('cash','card','transfer','online')` |
| `payments` | Payment line items | `transaction_type IN ('charge','payment','refund')`; `amount != 0` (allows negative refund) |
| [competitions](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/competitions/repository.py#36-39) | Competition events | |
| `competition_categories` | Categories within a competition | `ON DELETE CASCADE` from competition |
| [teams](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/competitions/repository.py#141-144) | Team per category | `enrollment_fee_per_student` can be NULL or float > 0 |
| [team_members](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/competitions/service.py#212-231) | Students in teams | `UNIQUE(team_id, student_id)`; `fee_paid BOOLEAN` |

### 3.3 Views (5)

| View | What it gives you |
|---|---|
| `v_students` | students + primary guardian name/phone joined |
| `v_enrollment_balance` | enrollment_id + `net_due`, `total_paid`, [balance](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/finance/repository.py#127-137) (live, computed from payments) |
| `v_enrollment_attendance` | enrollment_id + `sessions_attended`, `sessions_missed` |
| `v_siblings` | pairs of students who share a guardian |
| `v_group_session_count` | group_id + level -> `regular_sessions`, `extra_sessions`, `total_sessions` |

> **Critical:** `v_enrollment_balance.balance` is calculated as [(amount_due - discount) - net_paid](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/competitions/models.py#34-45). The column is a PostgreSQL `Decimal` type — always cast to `float()` in Python before arithmetic.

---

## 4. Module Architecture

Each module follows a strict **3-layer pattern**:

```
models.py       SQLModel ORM class (maps to DB table)
repository.py   Pure data access — accepts Session, returns ORM objects or dicts
service.py      Business logic — opens sessions via get_session(), calls repo, raises ValueError on validation failure
```

The UI imports **only from [service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py)**, never directly from [repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py).

---

## 5. Module Reference

### 5.1 `app/modules/auth`

**Models:** `User` (table: `users`)

**service.py:**
- `authenticate(username, password) -> User | None`
- `create_user(data) -> User`

**Auth flow:** Login page sets `st.session_state["user"]`. All pages call `require_auth()` from `auth_guard.py` at the top.

---

### 5.2 `app/modules/crm` — Students & Guardians

> **Naming convention:** DB table and model = `guardians`/`Guardian`. UI text = "Parent". Python function names retain `guardian` to avoid breaking imports.

**Models:** `Guardian`, `Student`, `StudentGuardian`

**repository.py:**
| Function | Notes |
|---|---|
| `create_guardian(session, guardian)` | |
| `get_guardian_by_id(session, id)` | |
| `get_guardian_by_phone(session, phone)` | Used for dedup |
| `search_guardians(session, query)` | ilike on name + both phones, limit 50 |
| `create_student(session, student)` | |
| `get_student_by_id(session, id)` | |
| `search_students(session, query)` | ilike on full_name, limit 50 |
| `get_student_guardians(session, student_id)` | Returns junction objects |
| `link_guardian(session, student_id, guardian_id, relationship, is_primary)` | |
| `get_siblings(session, student_id)` | Uses `v_siblings` view |

**service.py:**
| Function | Notes |
|---|---|
| `validate_phone(phone)` | Strips non-digits, checks min length 10 |
| `register_guardian(data)` | Raises if phone already exists |
| `find_or_create_guardian(data) -> (Guardian, bool)` | Preferred registration entry point |
| `search_guardians(query)` | Min 2 chars |
| `register_student(student_data, guardian_id, relationship)` | Returns (student, siblings) |
| `search_students(query)` | Min 2 chars |
| `find_siblings(student_id)` | |
| `get_guardian_students(guardian_id)` | Returns active students linked to guardian |

---

### 5.3 `app/modules/academics` — Courses & Groups

**Models:** `Course`, `Group`, `CourseSession` (in `session_models.py` — NOT `models.py`)

**Important field name:** `Group.level_number` is the group's current active level. NOT `current_level`.

**Service time window constraint:** Groups must be scheduled between **11:00 AM and 9:00 PM**.

**service.py:**
| Function | Notes |
|---|---|
| `add_new_course(data)` | Validates price > 0, sessions_per_level > 0, name unique |
| `update_course_price(course_id, new_price)` | |
| `get_active_courses()` | |
| `schedule_group(data)` | Creates group + auto-generates name "{Day} {Time} - {Course}" + generates level 1 sessions |
| `get_groups_by_course(course_id)` | Active only |
| `get_all_active_groups(include_inactive=False)` | Pass True to include completed/cancelled |
| `get_all_active_groups_enriched()` | Returns dicts with instructor_name, course_name |
| `get_todays_groups_enriched()` | Groups with a session today |
| `get_group_by_id(group_id)` | |
| `generate_level_sessions(group_id, level_number, start_date)` | Raises if sessions already exist |
| `add_extra_session(group_id, level_number, extra_date, notes)` | Inserts numbered extra session |
| `delete_session(session_id)` | |
| `mark_substitute_instructor(session_id, instructor_id)` | |
| `list_group_sessions(group_id, level_number)` | |
| `check_level_complete(group_id, level_number) -> bool` | |
| `advance_group_level(group_id)` | Increments `groups.level_number` |

---

### 5.4 `app/modules/enrollments`

**Model:** `Enrollment`

`enrollment.level_number` is a **snapshot** of `group.level_number` at time of enrollment.

**service.py:**
| Function | Notes |
|---|---|
| `enroll_student(student_id, group_id, amount_due, discount, notes, created_by) -> (Enrollment, capacity_exceeded: bool)` | Main entry; validates student active, group active, no duplicate, soft cap check |
| `get_student_enrollments(student_id)` | |
| `get_group_enrollments(group_id, status)` | |
| `transfer_enrollment(enrollment_id, target_group_id, ...)` | Sets old to 'transferred', creates new |
| `drop_enrollment(enrollment_id)` | Sets status to 'dropped' |

---

### 5.5 `app/modules/attendance`

**Valid statuses:** `present`, `absent`, `late`, `excused`  
Note: `unmarked` is a virtual status displayed in the UI when no attendance row exists.

**service.py:**
| Function | Notes |
|---|---|
| `mark_attendance(session_id, student_id, enrollment_id, status, marked_by)` | Upserts |
| `get_session_attendance(session_id)` | |
| `get_student_attendance(student_id, group_id, level_number)` | |

---

### 5.6 `app/modules/finance`

**Models:** `Receipt` (header), `Payment` (line items)

**transaction_type:** `payment`, `charge`, `refund`  
**payment_type:** `course_level`, `competition`, `other`  
**Auto receipt_number format:** `REC-{year}-{zero-padded-id}` (e.g. `REC-2026-00042`)

**service.py:**
| Function | Notes |
|---|---|
| `open_receipt(guardian_id, method, received_by_user_id, notes) -> Receipt` | Creates header + assigns number |
| `add_charge_line(receipt_id, student_id, enrollment_id, amount, payment_type, discount, notes)` | Validates enrollment is active |
| `finalize_receipt(receipt_id) -> dict` | Validates >= 1 line |
| `refund_receipt(receipt_id, reason)` | Creates mirror refund lines — does NOT delete original |
| `get_receipt_with_lines(receipt_id) -> dict` | Returns {receipt, lines} |
| `get_student_balance(student_id)` | Uses v_enrollment_balance |
| `get_guardian_receipts(guardian_id)` | |
| `search_receipts(query)` | By receipt number or student name |

---

### 5.7 `app/modules/competitions`

**Models:** `Competition`, `CompetitionCategory`, `Team`, `TeamMember`  
**Hierarchy:** Competition -> CompetitionCategory -> Team -> TeamMember

**Business rules:**
- A student can only be in one team per category (`UNIQUE(team_id, student_id)`)
- Uniqueness across competition enforced at service layer
- Teams with `enrollment_fee_per_student = NULL` or 0 auto-mark `fee_paid = True`

**service.py:**
| Function | Notes |
|---|---|
| `get_student_competitions(student_id) -> list[dict]` | Returns {membership, team, category, competition} per row |
| `create_competition(name, edition, competition_date, location, notes)` | |
| `list_competitions()` | |
| `update_competition(competition_id, **kwargs)` | |
| `delete_competition(competition_id)` | |
| `add_category(competition_id, category_name, notes)` | |
| `update_category(category_id, **kwargs)` | |
| `delete_category(category_id)` | |
| `create_team(category_id, team_name, group_id, coach_id, fee_per_student)` | |
| `update_team(team_id, **kwargs)` | |
| `delete_team(team_id)` | |
| `add_member_to_team(team_id, student_id) -> TeamMember` | Validates no duplicate across competition |
| `remove_member_from_team(team_id, student_id)` | |
| `mark_team_fee_paid(team_id, student_id, receipt_id, payment_id)` | Links payment to team_member |

---

### 5.8 `app/modules/analytics` (Phase 6)

All functions return `list[dict]` or scalar. Always `float()` cast monetary columns.

**repository.py:**
| Function | Key columns returned |
|---|---|
| `get_active_enrollment_count(db) -> int` | |
| `get_today_sessions(db, target_date)` | session_id, course_name, group_name, instructor_name, present, absent, unmarked, total_enrolled |
| `get_today_unpaid_attendees(db, target_date)` | student_id, student_name, guardian_name, phone_primary, total_balance |
| `get_revenue_by_date(db, start, end)` | day, net_revenue |
| `get_revenue_by_method(db, start, end)` | payment_method, net_revenue, receipt_count |
| `get_outstanding_by_group(db)` | group_id, group_name, course_name, students_with_balance, total_outstanding |
| `get_top_debtors(db, limit=10)` | student_id, student_name, guardian_name, phone_primary, total_outstanding |
| `get_group_roster(db, group_id, level_number)` | student_id, student_name, enrollment_id, balance, sessions_attended, attendance_pct |
| `get_attendance_heatmap(db, group_id, level_number)` | student_id, student_name, session_id, session_number, session_date, status |
| `get_competition_fee_summary(db)` | competition_id, competition_name, team_count, member_count, fees_collected, fees_outstanding |

**service.py:** Identical names, no `db` arg — each opens its own session via `get_session()`.

---

## 6. UI Architecture

### 6.1 Sidebar Navigation (`app/ui/main.py`)
- 🏠 Dashboard -> `pages/0_Dashboard.py`
- 💳 Finance -> `pages/7_Finance.py`
- 🏆 Competitions -> `pages/8_Competitions.py`
- 📊 Reports -> `pages/9_Reports.py`

Other pages (Student, Parent, Course, Group, Enrollment) are reached programmatically via `st.switch_page()`.

> **Note:** There is no page `6_`. Finance is `7_Finance.py`.

### 6.2 Session State Navigation Pattern

```python
# Sender:
st.session_state["nav_target_student_id"] = student.id
st.switch_page("pages/2_Student_Management.py")

# Receiver page:
if "nav_target_student_id" in st.session_state:
    render_student_detail(st.session_state.pop("nav_target_student_id"))
else:
    render_student_overview()
```

**Active navigation keys:**
| Key | Used by |
|---|---|
| `nav_target_student_id` | Student detail from any page |
| `nav_target_parent_id` | Guardian/Parent detail |
| `nav_target_group_id` | Group detail from Dashboard |
| `nav_target_course_id` | Course detail |
| `user` | Auth session — set by login.py |

### 6.3 Pages

| File | Default View | Detail Trigger |
|---|---|---|
| `0_Dashboard.py` | KPIs + sessions + revenue | Click row -> nav_target_group_id |
| `1_Parent_Management.py` | parent_overview | nav_target_parent_id |
| `2_Student_Management.py` | student_overview | nav_target_student_id |
| `3_Course_Management.py` | course_overview | nav_target_course_id |
| `4_Group_Management.py` | group_overview | nav_target_group_id |
| `5_Enrollment.py` | Enrollment form | inline |
| `7_Finance.py` | finance_overview | inline |
| `8_Competitions.py` | competition_overview | inline |
| `9_Reports.py` | 4-tab reports | Click debtor -> nav_target_student_id |
| `login.py` | Login form | — |

### 6.4 Components

| File | Renders |
|---|---|
| `auth_guard.py` | `require_auth()` — redirects to login if no session |
| `parent_overview.py` | Searchable guardian list |
| `parent_detail.py` | Guardian profile: info, linked students, balances, competition fees |
| `student_overview.py` | Searchable student list |
| `student_detail.py` | Student profile: info, guardian, enrollments, competition history |
| `course_overview.py` | Course list + create form |
| `course_detail.py` | Course info + groups |
| `group_overview.py` | Group list + schedule |
| `group_detail.py` | Group: students, sessions, attendance |
| `attendance_grid.py` | Per-session attendance marking grid |
| `finance_overview.py` | Balance search + receipt log |
| `finance_receipt.py` | Receipt creation wizard |
| `competition_overview.py` | Competitions list, create form, categories/teams |
| `competition_detail.py` | Deep competition view with inline edit/delete |

---

## 7. Architectural Decision Records

| # | Decision | Rationale |
|---|---|---|
| ADR-1 | Streamlit, no REST API | Internal tool, single-server, avoids API overhead |
| ADR-2 | SQLModel (not raw SQLAlchemy) | Pydantic validation + SQLAlchemy engine in one |
| ADR-3 | `get_session()` as context manager | Auto-commit on exit, rollback on exception; `expire_on_commit=False` |
| ADR-4 | `enrollment.level_number` is a snapshot | Students join at the current group level; historical records stable |
| ADR-5 | `student_guardians` junction table | Allows M:M, sibling detection via `v_siblings` view |
| ADR-6 | Receipts as headers + Payment line items | One receipt can pay multiple students; refunds are new rows not deletions |
| ADR-7 | NULL/zero-fee teams auto-mark paid | Academy-sponsored teams need no student payment |
| ADR-8 | Guardian (code) vs Parent (UI) naming | Controlled rename — Python function names kept as `guardian` to avoid import breakage |
| ADR-9 | Analytics uses raw SQL (`text()`) | Multi-table aggregations and window functions are cleaner in raw SQL |

---

## 8. Standard Workflows

### Finance Flow
```
1. open_receipt(guardian_id, method, user_id)        -> Receipt
2. add_charge_line(receipt_id, student_id, ...)      -> Payment (repeat per student)
3. finalize_receipt(receipt_id)                      -> dict summary
4. (Competition) mark_team_fee_paid(team_id, ...)
5. (Refund) refund_receipt(receipt_id, reason)       -> creates mirror rows, no deletion
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

## 9. Common Pitfalls

1. **`Decimal` + `float` crash** — PostgreSQL returns `DECIMAL` as `decimal.Decimal`. Always: `float(value)` before arithmetic.
2. **`group.current_level` does NOT exist** — the field is `group.level_number`.
3. **`search_Parents` / `list_groups` do NOT exist** — correct names: `search_guardians`, `get_all_active_groups()`.
4. **Session state navigation** — use `.pop("nav_key")` not `.get()` in the detail receiver page.
5. **`st.switch_page()` path** — must exactly match the filename including the number prefix (e.g., `"pages/2_Student_Management.py"`).
6. **`expire_on_commit=False`** — objects are safe after session closes, but don't share across threads.
7. **Zero-fee teams** — check `team.enrollment_fee_per_student is None or == 0` before showing Pay button.
8. **`CourseSession` model location** — it is in `session_models.py`, NOT `models.py`, to avoid circular imports.
9. **`session` shadows Python's `with Session`** — all repo functions use `session` as the parameter name but this is the SQLModel `Session` object (database session), not an HTTP session.
10. **Analytics columns need `.rename(columns={...})`** — never rename by position (`df.columns = [...]`) since SQLAlchemy dict key order is not guaranteed.

---

## 10. Dev Environment

```bash
# Start app
python run_app.py

# DB connection (.env)
DATABASE_URL=postgresql://user:password@localhost:5432/techno_kids

# Schema reset (destructive)
psql $DATABASE_URL -f db/schema.sql

# Activate venv (Windows)
.venv\Scripts\activate
```

**Key dependencies:**
- `streamlit` — UI framework
- `sqlmodel` — ORM (wraps SQLAlchemy)
- `psycopg2-binary` — PostgreSQL adapter
- `python-dotenv` — .env loading
- `bcrypt` — Password hashing
- `pandas` — Dataframes in Dashboard/Reports pages

---

## 11. Phase History

| Phase | Features Added |
|---|---|
| 1 | DB schema, student/guardian CRUD |
| 2 | Course catalog, group scheduling, session generation |
| 3 | Enrollment workflow with level snapshots |
| 4 | Finance: receipts, payments, balance views |
| 5 | Competitions module (teams, categories, fees); parent profile shows competition fees |
| 5 Polish | Inline edit/delete for competitions; "Guardian" -> "Parent" UI rename; wide layout |
| 6 | Analytics module; live Dashboard; 4-tab Reports page (Financial/Academic/Competitions/Heatmap); CSV export; historical date filter; active enrollments KPI; debtor cross-link |
