# Phase 3 — Technical Plan: Daily Operations

---

## 1. Scope & Objective

Phase 3 implements the core daily workflow: enrolling students in groups, scheduling sessions, and marking attendance.

**Key Deliverables:**

- Ability to enroll a student in a group (with level snapshot, capacity check, and sibling discount application).
- Ability to generate the sessions for a level from a group's schedule defaults.
- Ability to mark attendance for a full class in one operation.
- Ability to transfer, drop, or complete an enrollment.

**Modules Touched:**

- `app/modules/enrollments/` (NEW)
- `app/modules/attendance/` (NEW)
- `app/modules/academics/` (session additions to existing module)
- `app/ui/pages/` (3 new Streamlit pages)

---

## 2. File-by-File Breakdown: `enrollments` Module

### `app/modules/enrollments/models.py`

Mirrors the `enrollments` table from schema v3.2.

```python
class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    group_id: int = Field(foreign_key="groups.id")
    level_number: int                           # Snapshot from group at enrollment time
    enrolled_at: Optional[datetime] = None
    amount_due: Optional[float] = None          # Custom amount per student (can differ from course price)
    discount_applied: float = 0.0
    status: str = "active"                      # CHECK: active / completed / transferred / dropped
    transferred_from: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    notes: Optional[str] = None
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### `app/modules/enrollments/repository.py`

Pure DB operations, no business logic.

| Function | Description |
|---|---|
| `create_enrollment(session, enrollment)` | Inserts enrollment row, returns it |
| `get_enrollment(session, enrollment_id)` | Returns `Enrollment \| None` |
| `get_active_enrollment(session, student_id, group_id)` | Returns active enrollment or `None` (guards against duplicate enrollment) |
| `list_enrollments(session, group_id, level_number, status)` | Returns filterable list |
| `update_enrollment_status(session, enrollment_id, status)` | Updates status field |
| `update_discount(session, enrollment_id, discount)` | Updates `discount_applied` field |

### `app/modules/enrollments/service.py`

Business logic entry point — opens its own sessions, manages the full enrollment workflow.

**`enroll_student(student_id, group_id, amount_due, discount) -> Enrollment`**
Ordered checks before inserting:

1. Fetch student → raise if not found or `is_active = False`
2. Fetch group → raise if not found or `status != 'active'`
3. Count active enrollments vs `group.max_capacity` → warn (not block; admin override allowed)
4. Check `get_active_enrollment(student_id, group_id)` → raise if already enrolled
5. Snapshot `group.level_number` into `enrollment.level_number`
6. Set `enrollment.enrolled_at = today`
7. Insert and return the enrollment

**`apply_sibling_discount(enrollment_id) -> Enrollment`**

- Loads enrollment, sets `discount_applied = 50.0`
- Calls `repo.update_discount()`

**`transfer_student(from_enrollment_id, to_group_id) -> Enrollment`**

1. Load source enrollment → raise if not active
2. Mark source as `transferred`
3. Create new enrollment in `to_group_id` with `transferred_from = from_enrollment_id`, same `amount_due`
4. Return the new enrollment

**`drop_enrollment(enrollment_id) -> Enrollment`**

- Sets status to `dropped` (preserves all financial history)

**`complete_enrollment(enrollment_id) -> Enrollment`**

- Sets status to `completed`

---

## 3. File-by-File Breakdown: Session additions to `academics` module

New functions added to the **existing** `app/modules/academics/repository.py` and `service.py`.

### Repository additions

| Function | Description |
|---|---|
| `create_session(session, sess)` | Inserts a single session row |
| `list_sessions(session, group_id, level_number)` | Ordered by `session_number` |
| `get_session_by_id(session, session_id)` | Returns `Session \| None` |
| `count_sessions(session, group_id, level_number)` | Returns count of regular sessions for a level |
| `update_session_instructor(session, session_id, instructor_id)` | Sets `actual_instructor_id` + `is_substitute=True` |

### Service additions

**`generate_level_sessions(group_id, level_number, start_date) -> list[Session]`**

- Fetches group + course
- Creates N sessions (where N = `course.sessions_per_level`) spaced weekly on `group.default_day`
- Each session inherits `default_time_start` / `default_time_end` from the group
- Returns list of created sessions

**`add_extra_session(group_id, level_number, date) -> Session`**

- Creates a session with `is_extra_session = True` and the next available `session_number`

**`mark_substitute_instructor(session_id, instructor_id) -> Session`**

- Sets `actual_instructor_id` and `is_substitute = True`

### New SQLModel for `sessions` table

```python
class CourseSession(SQLModel, table=True):  # Named CourseSession to avoid stdlib conflict
    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id")
    level_number: int
    session_number: int
    session_date: datetime                    # DB is DATE
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    actual_instructor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    is_substitute: bool = False
    is_extra_session: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
```

> **Note:** Named `CourseSession` (not `Session`) to avoid clashing with Python's built-in `session` objects and SQLModel's `Session` class.

---

## 4. File-by-File Breakdown: `attendance` Module

### `app/modules/attendance/models.py`

```python
class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    session_id: int = Field(foreign_key="sessions.id")
    enrollment_id: int = Field(foreign_key="enrollments.id")
    status: str                               # CHECK: present / absent / late / excused
    marked_by: Optional[int] = Field(default=None, foreign_key="users.id")
    marked_at: Optional[datetime] = None
```

### `app/modules/attendance/repository.py`

| Function | Description |
|---|---|
| `upsert_attendance(session, record)` | INSERT or UPDATE on `UNIQUE(student_id, session_id)` |
| `get_session_attendance(session, session_id)` | Returns all `Attendance` rows for a session |
| `get_enrollment_attendance(session, enrollment_id)` | Returns `{sessions_attended, sessions_missed}` from `v_enrollment_attendance` view |

### `app/modules/attendance/service.py`

**`mark_session_attendance(session_id, student_statuses_dict, marked_by_user_id) -> int`**
Where `student_statuses_dict` = `{student_id: "present" | "absent" | "late" | "excused"}`.

Logic:

1. Fetch the session → raise if not found
2. For each student in the dict:
   - Look up their active enrollment for this session's `group_id + level_number`
   - If no enrollment found, **skip and collect** as a warning (don't abort the whole batch)
3. Bulk-upsert attendance records
4. Returns count of records successfully written

**`get_attendance_summary(enrollment_id) -> dict`**

- Queries `v_enrollment_attendance` view
- Returns `{enrollment_id, sessions_attended, sessions_missed}`

---

## 5. File Interaction Map

```text
UI: 5_Attendance.py
  └──► attendance.service.mark_session_attendance(session_id, {student_id: status})
         │
         ├──► academics.repository.get_session_by_id()   [validate session exists]
         │
         ├──► enrollments.repository.get_active_enrollment(student_id, group_id, level)
         │       [resolve enrollment_id for each student]
         │
         └──► attendance.repository.upsert_attendance()  [batch insert/update]
```

---

## 6. UI Pages

### `app/ui/pages/4_Enrollment.py`

**Mission:** Enroll students in a group, apply sibling discount, transfer, and drop.

**Tabs:**

- **Enroll Student**: Search student + Select group → auto-shows level, price, capacity status. Submit enrolls.
- **Manage Enrollment**: Search existing enrollment → buttons for Apply Discount / Transfer / Drop / Complete.

### `app/ui/pages/5_Sessions.py`

**Mission:** Manage the sessions for a group level.

**Layout:**

- Select group + level → show existing sessions table.
- Button: **Generate Sessions** (triggers `generate_level_sessions` with a start date picker).
- Button: **Add Extra Session** (date picker inline).
- On each session row: **Mark Substitute** (select replacement instructor).

### `app/ui/pages/6_Attendance.py`

**Mission:** Mark attendance for one session.

**Flow:**

1. Select group → sessions for that group appear.
2. Select session → roster of enrolled students for that group+level appears.
3. Each student has a radio: `present / absent`.
4. Submit → calls `mark_session_attendance()`.
5. Summary shown: `X present, Y absent`.

---

## 7. Phase 3 Completion Checklist

- [ ] `app/modules/enrollments/__init__.py`
- [ ] `app/modules/enrollments/models.py`
- [ ] `app/modules/enrollments/repository.py`
- [ ] `app/modules/enrollments/service.py`
- [ ] `app/modules/academics/models.py` — add `CourseSession` model
- [ ] `app/modules/academics/repository.py` — session CRUD additions
- [ ] `app/modules/academics/service.py` — `generate_level_sessions`, `add_extra_session`, `mark_substitute_instructor`
- [ ] `app/modules/attendance/__init__.py`
- [ ] `app/modules/attendance/models.py`
- [ ] `app/modules/attendance/repository.py`
- [ ] `app/modules/attendance/service.py`
- [ ] `app/ui/pages/4_Enrollment.py`
- [ ] `app/ui/pages/5_Sessions.py`
- [ ] `app/ui/pages/6_Attendance.py`
