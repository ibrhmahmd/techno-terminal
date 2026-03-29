> ⚠️ **STALE DOCUMENT — Historical Reference Only**  
> Phase statuses below have been corrected (2026-03-24). The implementation details may predate later refactors.  
> For the authoritative state see [`docs/MEMORY_BANK.md §12`](../../MEMORY_BANK.md) and [`docs/reviews/sprint_roadmap_post_qa_2026.md`](../../reviews/sprint_roadmap_post_qa_2026.md).

# Techno Terminal — Detailed Feature Breakdown by Phase

## Architecture Decision: Module-per-Feature

*(See `04_architecture/01_architecture_decision.md` for full comparison)*

Each business module contains exactly: `models.py` · `repository.py` · `service.py`
The Streamlit UI layer consumes services directly. A future FastAPI layer will use the same services.

```
modules: crm · academics · enrollments · attendance · finance · competitions
```

> **Status as of March 2026:**
>
> - ✅ Phase 1 — Core Foundation & Security: **COMPLETE**
> - ✅ Phase 2 — CRM Core: **COMPLETE**
> - ✅ Phase 3 — Daily Operations: **COMPLETE** (with full UX overhaul)
> - ✅ Phase 4 — Financial Ledger: **COMPLETE**
> - ✅ Phase 5 — Competitions & Teams: **COMPLETE** _(updated 2026-03-24)_
> - ✅ Phase 6 — Reporting & Analytics: **COMPLETE** _(updated 2026-03-24)_

---

## Phase 1 — Core Foundation & Security

> **Goal:** A running Streamlit shell with DB connectivity, auth, and the visual skeleton in place.
> **Modules touched:** `db/`, `modules/auth/`, `ui/`

### 1.1 Project Bootstrap

- Create `src/` directory structure matching the Module-per-Feature layout
- Set up `pyproject.toml` / `requirements.txt` with dependencies:
  `streamlit`, `sqlmodel`, `psycopg2-binary`, `python-dotenv`, `passlib`
- Create `.env` with `DATABASE_URL`, `SECRET_KEY`
- Create `db/connection.py`: SQLModel engine factory, `get_session()` context manager
- Create `db/base.py`: shared `SQLModel` base

### 1.2 Database Initialization

- Run `db/schema.sql` against a fresh PostgreSQL database
- Verify all 16 tables, 5 views, and indexes are created
- Insert seed admin user (handled by the last lines of `schema.sql`)

### 1.3 Auth Module (`modules/auth/`)

- `models.py`: `User`, `Employee` SQLModel definitions (read-only at this stage)
- `repository.py`: `get_user_by_username(username)` — returns `User | None`
- `service.py`:
  - `authenticate(username, password) → User | None` (using `passlib` to verify hash)
  - `change_password(user_id, new_password)` — hashes and saves

### 1.4 Streamlit Shell (`ui/`)

- `main.py`: App entry point with sidebar navigation
- Session state management: `st.session_state.current_user`, `st.session_state.authenticated`
- Login page: username/password form → calls `auth_service.authenticate()` → sets session state
- Auth guard: every page checks `st.session_state.authenticated`, redirects to login if not
- Sidebar: navigation links per role (`admin` sees all, future roles see subset)
- Placeholder pages for each of the 6 modules

---

## Phase 2 — CRM Core

> **Goal:** Administrators can fully manage families, students, and the course catalogue.
> **Modules touched:** `modules/crm/`, `modules/academics/`

### 2.1 Guardian Management (`modules/crm/`)

- `models.py`: `Guardian` SQLModel (id, full_name, phone_primary, phone_secondary, email, relation, notes)
- `repository.py`:
  - `create_guardian(data)` — inserts, returns `Guardian`
  - `get_guardian(id)` — returns `Guardian | None`
  - `search_guardians(query)` — searches `full_name` and `phone_primary` (ILIKE)
  - `update_guardian(id, data)` — partial update, backend sets `updated_at`
  - `list_guardians(page, page_size)` — paginated list
- `service.py`:
  - `register_guardian(data)` — validates required fields, calls repo
  - `find_or_create_guardian(phone, full_name)` — prevents duplicate guardian creation
  - `update_guardian_contact(id, data)` — validates phone format, calls repo

### 2.2 Student Management (`modules/crm/`)

- `models.py`: `Student`, `StudentGuardian` SQLModel definitions
- `repository.py`:
  - `create_student(data)` — returns `Student`
  - `link_guardian(student_id, guardian_id, relationship, is_primary)`
  - `get_student(id)` — returns full student + primary guardian via `v_students` view
  - `search_students(query)` — searches name
  - `list_students(is_active, page, page_size)` — filterable
  - `deactivate_student(id)` — sets `is_active = FALSE` (soft delete)
  - `get_siblings(student_id)` — queries `v_siblings` view
- `service.py`:
  - `register_student(student_data, guardian_id, relationship)` — validates DOB, links guardian
  - `add_secondary_guardian(student_id, guardian_id, relationship)` — validates no duplicate link
  - `detect_siblings(student_id)` — returns list of sibling students via view
  - `deactivate_student(id)` — checks for active enrollments before allowing deactivation

### 2.3 Course Management (`modules/academics/`)

- `models.py`: `Course`, `Group` SQLModel definitions
- `repository.py`:
  - `create_course(data)`, `update_course(id, data)`, `list_courses(is_active)`
  - `create_group(data)`, `update_group(id, data)`, `list_groups(status, course_id)`
  - `get_group_capacity_used(group_id)` — `COUNT` of active enrollments vs max_capacity
- `service.py`:
  - `create_course(data)` — validates `price > 0`, `sessions_per_level > 0`
  - `create_group(course_id, instructor_id, level, schedule)` — validates time constraints (`start < end`)
  - `advance_group_to_next_level(group_id)` — increments `level_number` on the group, does NOT touch existing enrollment records

---

## Phase 3 — Daily Operations ✅ COMPLETE

> **Goal:** The core daily workflow — enrolling students, scheduling sessions, and marking attendance.
> **Modules touched:** `modules/enrollments/`, `modules/attendance/`, `modules/academics/` (sessions)
> **Technical plan:** See `07_phase3_technical_plan.md`

### Phase 3 Completion Notes

All backend services and UI pages were implemented. Additionally, a major **UX Overhaul** was performed that restructured **all entity management pages** (Groups, Students, Parents, Courses) into a unified **Overview → Detail** pattern:

- **Overview page:** search/filter bar + summary table → clicking a row sets a session state key and reruns
- **Detail page:** renders the selected entity with full management controls; Back button clears session state

**Specific Group Management changes:**

- `group_overview.py`: 7-day filter buttons (one per weekday) replace the old "Today's Groups" query. Groups are now filtered by their `default_day` field, not by session date joins — this fixed a bug where newly created groups were invisible.
- `group_detail.py`: Separate session list was removed. Session delete buttons and instructor names were moved directly into the attendance grid column headers.
- `attendance_grid.py`: Headers now show: session number + instructor name + session date + delete button. Student name buttons navigate to the Student Detail page.

**Components created:**

- `app/ui/components/group_overview.py`
- `app/ui/components/group_detail.py`
- `app/ui/components/attendance_grid.py`
- `app/ui/components/student_overview.py`
- `app/ui/components/student_detail.py`
- `app/ui/components/parent_overview.py`
- `app/ui/components/parent_detail.py`
- `app/ui/components/course_overview.py`
- `app/ui/components/course_detail.py`

---

### 3.1 Enrollment Management (`modules/enrollments/`)

- `models.py`: `Enrollment` SQLModel definition
- `repository.py`:
  - `create_enrollment(data)` — inserts with level snapshot
  - `get_enrollment(id)` — returns enrollment
  - `get_active_enrollment(student_id, group_id)` — returns active enrollment or `None`
  - `list_enrollments(group_id, level_number, status)` — filterable
  - `update_enrollment_status(id, status)` — 'completed', 'dropped', 'transferred'
- `service.py`:
  - `enroll_student(student_id, group_id, amount_due, discount)`:
    1. Checks student is active
    2. Checks group status is 'active'
    3. Checks group capacity not exceeded
    4. Checks no existing active enrollment in same group (partial unique index will catch it too)
    5. Snapshots `level_number` from group at time of enrollment
    6. Inserts enrollment
  - `apply_sibling_discount(enrollment_id)` — validates sibling link, applies 50 EGP discount
  - `transfer_student(from_enrollment_id, to_group_id)` — marks old as 'transferred', creates new enrollment with `transferred_from` link
  - `complete_enrollment(enrollment_id)` — validates balance is zero, marks 'completed'
  - `drop_enrollment(enrollment_id)` — marks 'dropped' (financial record preserved)

### 3.2 Session Scheduling (`modules/academics/`)

- `repository.py` additions:
  - `create_session(data)` — takes `group_id`, `level_number`, `session_number`, date/time
  - `list_sessions(group_id, level_number)` — ordered by `session_number`
  - `get_session(id)` — returns session
- `service.py` additions:
  - `generate_level_sessions(group_id, level_number, start_date)` — creates sessions 1-N using `course.sessions_per_level`, spacing by `group.default_day`, auto-assigning `start/end_time` from group defaults
  - `add_extra_session(group_id, level_number, date)` — creates extra session with `is_extra_session=TRUE`
  - `mark_substitute_instructor(session_id, instructor_id)` — updates `actual_instructor_id` and sets `is_substitute=TRUE`

### 3.3 Attendance Marking (`modules/attendance/`)

- `models.py`: `Attendance` SQLModel
- `repository.py`:
  - `mark_attendance(student_id, session_id, enrollment_id, status, marked_by)` — inserts or updates (upsert on `UNIQUE(student_id, session_id)`)
  - `get_session_attendance(session_id)` — returns all attendance rows for a session
  - `get_enrollment_attendance(enrollment_id)` — queries `v_enrollment_attendance` view
  - `bulk_mark_attendance(session_id, records)` — batch insert for marking a full class
- `service.py`:
  - `mark_session_attendance(session_id, student_statuses, marked_by_user_id)`:
    1. Validates session exists
    2. For each student: resolves their active `enrollment_id` for this session's group+level
    3. Rejects if `enrollment_id` can't be resolved (student not enrolled)
    4. Calls `repo.bulk_mark_attendance()`
  - `get_attendance_summary(enrollment_id)` — returns sessions attended, missed from view

---

## Phase 4 — Financial Ledger ✅ COMPLETE

> **Goal:** Full accounting at the point of collection — receipts, split payments, balance tracking, and refunds.
> **Module touched:** `modules/finance/`
> **Technical plan:** See `08_phase4_technical_plan.md`

### Phase 4 Completion Notes

All backend services, repository functions, and UI pages were implemented.

**Key design decisions:**

- A single receipt can cover multiple children of the same guardian (parent pays for all kids at once)
- No `total_amount` stored on receipts — always derived from `payments` rows via `v_enrollment_balance` view
- `transaction_type`: `'payment'` = money in, `'charge'` = obligation, `'refund'` = money out (all amounts positive)
- Receipt numbers formatted as `TK-YYYY-{id:05d}`

**Cross-module integration added:**

- `student_detail.py` — Balance column added to the enrollment table; Pay Now shortcut button
- `parent_detail.py` — Financial Overview section shows per-child balance status; Create Receipt button
- Daily Summary receipt table is clickable and opens the Receipt Detail view

---

### 4.1 Point of Sale — Receipt Creation

- `models.py`: `Receipt`, `Payment` SQLModel definitions
- `repository.py`:
  - `create_receipt(guardian_id, method, received_by, paid_at)` — returns `Receipt`
  - `generate_receipt_number(receipt_id)` — formats `TK-YYYY-{id:05d}`
  - `add_payment_line(receipt_id, student_id, enrollment_id, amount, transaction_type, payment_type, discount)` — inserts payment row
  - `get_receipt_with_lines(receipt_id)` — receipt + all linked payments
  - `get_receipt_total(receipt_id)` — `SUM(payments.amount WHERE type IN ('payment','charge')) - SUM(... WHERE type='refund')`
- `service.py`:
  - `open_receipt(guardian_id, method, received_by)` — creates the receipt header
  - `add_charge_line(receipt_id, student_id, enrollment_id, amount, payment_type, discount)` — validates enrollment is active, inserts payment row with `transaction_type='charge'` (the obligation) or `'payment'`(settling it)
  - `finalize_receipt(receipt_id)` — validates at least 1 payment line exists, returns receipt summary
  - `void_receipt(receipt_id)` — validates no settled payments, deletes header (ON DELETE RESTRICT enforces data safety on payments)

### 4.2 Balance & Reporting

- `repository.py` additions:
  - `get_enrollment_balance(enrollment_id)` — queries `v_enrollment_balance` view
  - `get_student_balances(student_id)` — all enrollments with outstanding balance
  - `list_unpaid_enrollments(group_id)` — list of students with `balance > 0`
- `service.py` additions:
  - `get_student_financial_summary(student_id)` — returns balances across all active enrollments
  - `get_daily_collections(date)` — sum of payments received on a date grouped by method

### 4.3 Refunds

- `service.py` additions:
  - `issue_refund(enrollment_id, amount, reason, received_by)`:
    1. Opens a new receipt (`method` inherited from original)
    2. Adds a `payment` line with `transaction_type = 'refund'`
    3. Amount stored as positive value — the refund type signals direction
    4. Returns updated balance (should increase as money leaves)

---

## Phase 5 — Competitions & Teams

> **Goal:** Register teams for external competitions, track competition fees per student.
> **Module touched:** `modules/competitions/`

### 5.1 Competition Setup

- `models.py`: `Competition`, `CompetitionCategory`, `Team`, `TeamMember` SQLModel definitions
- `repository.py`:
  - `create_competition(name, edition, date, location)`
  - `add_category(competition_id, category_name)`
  - `list_competitions()`, `list_categories(competition_id)`

### 5.2 Team Management

- `repository.py` additions:
  - `create_team(category_id, group_id, team_name, coach_id, fee_per_student)` — `group_id` nullable
  - `add_team_member(team_id, student_id)` — inserts `TeamMember` with `fee_paid=FALSE`
  - `mark_fee_paid(team_id, student_id, payment_id)` — updates `fee_paid`, links payment
  - `list_team_members(team_id)` — returns members with fee status
- `service.py`:
  - `register_team(category_id, group_id, team_name, coach_id, student_ids, fee)`:
    1. Validates all students are active
    2. Creates team
    3. Adds each student as member
  - `pay_competition_fee(team_id, student_id, receipt_id, guardian_id)`:
    1. Creates payment line under the receipt with `payment_type='competition'`
    2. Marks `team_members.fee_paid = TRUE`, links `payment_id`

---

## Phase 6 — Reporting & Analytics

> **Goal:** Operational dashboards for daily management and periodic review.
> **Module:** No new module — reads from all other modules + DB views.

### 6.1 Operational Dashboards (Streamlit)

- **Today's View:** Sessions happening today, how many are marked present/absent, outstanding balances for today's attendees
- **Group Roster:** Full student list per group per level with attendance %, balance indicator
- **Financial Summary:** Daily/monthly revenue by payment method, outstanding dues by group

### 6.2 Student Profile Page (Streamlit)

- Full history: enrollments → sessions per level → attendance per session → payments
- All guardian contacts
- Sibling links
- Competition participations

### 6.3 Instructor View (future role gate)

- Sessions this week
- Attendance sheet for today's session
- (Read-only access, no financials)

---

## Dependency Order (Why These Phases Exist in This Sequence)

```
Auth → CRM (Guardian/Student) → Academics (Course/Group)
                                         ↓
                                   Enrollments ← links CRM + Academics
                                         ↓
                            Sessions (generated per group)
                                         ↓
                              Attendance ← requires Enrollment + Session
                                         ↓
                               Finance ← requires Receipt + Enrollment
                                         ↓
                            Competitions ← requires Student + Finance
                                         ↓
                              Analytics ← reads everything via views
```
