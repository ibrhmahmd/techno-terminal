# Techno Terminal — Full-Scale Architecture Review

> **Scope:** File structure, naming conventions, DB access strategy, scalability concerns, and vertical-slice migration path.  
> **Evidence based on:** Actual file readings across all 8 modules + UI layer.  
> **Date:** 2026-03-18

---

## 1. Current Architecture: What You Have

The project implements a **horizontal layered architecture** (also called N-tier or onion-lite). All modules share the same three-file pattern:

```
module/
├── models.py       ← ORM entity definition
├── repository.py   ← Data access functions
└── service.py      ← Business logic
```

This means the **layers are the organizational axis**, not the **features**. This is a classic approach — not inherently wrong — but it carries real scalability costs as the codebase grows.

---

## 2. Naming Convention Analysis

### 2.1 File Names — Collision Problem

Every single module has identically named files:

| File | Appears in |
|---|---|
| [models.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/models.py) | crm, academics, finance, enrollments, competitions, attendance, auth |
| [repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py) | all 8 modules |
| [service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py) | all 8 modules |

**What this causes:**
- In any stack trace, you see `service.py line 45` with **zero context** about which domain it belongs to
- IDE "go to definition" gets confused when multiple [models.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/models.py) files are open simultaneously
- When searching the codebase for `def create_` you get 20+ hits with no namespace disambiguation
- Import errors in Streamlit's flat-page model are common because Python path resolution relies on filenames

### 2.2 Special Anomaly: [session_models.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/session_models.py)

`academics/session_models.py` is the **only exception** to the naming convention — and the reason is architectural: `CourseSession` was split to break a circular import. This is a symptom of the deeper coupling problem (see §4.2). The current Memory Bank explicitly warns about this.

### 2.3 Function Name Inconsistencies Across Modules

The [repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py) files have no shared naming convention:

| Pattern Seen | Module |
|---|---|
| [create_parent](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py#10-14) | crm |
| [create_enrollment](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/repository.py#7-11) | enrollments |
| `create_receipt` | finance |
| `add_payment_line` | finance |
| `add_member_to_team` | competitions |
| [list_enrollments](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/repository.py#30-44) | enrollments |
| [search_students](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py#124-130) | crm |
| `list_active_courses` | academics |

There is no enforced [get_all](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/service.py#167-170), `get_by_id`, [create](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py#44-48), [update](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/repository.py#56-64), [delete](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/service.py#261-264) contract. Each repo invents its own naming.

---

## 3. Database Access Strategy: ORM vs Raw SQL

This codebase uses **both** — and the split is intentional but has inconsistencies.

### 3.1 ORM (SQLModel / SQLAlchemy) — Used for CRUD

All standard CRUD goes through SQLModel's `select()` + `session.exec()`:

```python
# crm/repository.py — ORM query
stmt = select(Parent).where(
    or_(
        Parent.full_name.ilike(search_term),
        Parent.phone_primary.ilike(search_term),
    )
).limit(50)
return session.exec(stmt).all()
```

**Verdict:** Correct use. Type-safe, IDE-friendly, automatically parameterized.

### 3.2 Raw SQL (`sqlalchemy.text()`) — Used for Aggregations and Views

The analytics module uses raw SQL exclusively:

```python
# analytics/repository.py — raw SQL
stmt = text("""
    SELECT ... COUNT(a.id) FILTER (WHERE a.status IN ('present', 'late')) AS present
    FROM sessions s
    JOIN groups g ON s.group_id = g.id
    ...
""")
```

**Also seen in [crm/repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py):**
```python
# Mixing raw SQL inside an otherwise ORM module
from sqlalchemy import text
stmt = text("SELECT sibling_id, sibling_name FROM v_siblings WHERE student_id = :student_id")
```

> [!NOTE]
> The ADR documents this explicitly (ADR-9). Raw SQL for complex aggregations and views is the right call — PostgreSQL-specific features like `FILTER (WHERE ...)`, `OVER (PARTITION BY ...)`, and `CROSS JOIN` for heatmaps are impossible to express cleanly in ORM.

### 3.3 The Hybrid Problem

The concern is that raw SQL leaks **into modules that should be ORM-only**. [crm/repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/repository.py) has a `from sqlalchemy import text` import buried at line 86, mid-file. This is not analytics — it is a view query that could be expressed in ORM via a `v_siblings` model but was short-cut with raw SQL. The boundary between "ORM module" and "raw SQL module" is implicit, not enforced.

### 3.4 [get_parent_students](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py#138-154) — Logic in Service Layer, Not Repo

In [crm/service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py) (lines 143-153):
```python
# Querying directly inside service.py bypassing repository
stmt = sql_select(StudentParent).where(...)
links = session.exec(stmt).all()
for link in links:
    s = session.get(Student, link.student_id)
```

This breaks the service→repository contract. The service opens sessions and writes queries directly. If this happens in `crm`, it will happen in 5 other modules next — and it did: [enrollments/service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/service.py) line 164 also does `select(Enrollment)` inline.

---

## 4. Vertical Slice Architecture vs Current Design

### 4.1 What Vertical Slice Would Look Like

Instead of organizing by **layer** (models / repo / service), you organize by **feature**:

```
modules/
├── crm/
│   ├── register_student/       ← one slice = one use case
│   │   ├── handler.py          ← entry point (called by UI)
│   │   ├── command.py          ← input DTO
│   │   └── query.py            ← read model
│   ├── search_students/
│   └── parent_profile/
├── enrollments/
│   ├── enroll_student/
│   ├── transfer_enrollment/
│   └── drop_enrollment/
```

Each slice is entirely self-contained. You don't share repositories across modules — each slice owns its data access.

### 4.2 Cross-Module Coupling — The Real Problem

The biggest scalability risk in this codebase is **cross-module imports**. Evidence from the actual code:

| Import | Location | Problem |
|---|---|---|
| `from app.modules.crm.repository import get_student_by_id` | `enrollments/service.py:3` | Enrollment service reaches into CRM's repo directly |
| `from app.modules.academics.repository import list_groups_by_course` | `enrollments/service.py:4` | Enrollment service reaches into Academics' repo |
| `from app.modules.enrollments.models import Enrollment` | `finance/service.py:5` | Finance service imports CRM model |
| `from app.modules.competitions.models import TeamMember` | `finance/service.py:124` | Finance performs competition logic inline |

**This is a dependency inversion violation.** The correct flow is:
```
finance.service → finance.repository → DB
```
But what's happening is:
```
finance.service → competition.models → (implicitly) competition's DB contract
```

If you ever rename `TeamMember.payment_id` or refactor the competitions module, [finance/service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/finance/service.py) silently breaks.

### 4.3 Does the Current Architecture Scale?

| Concern | Current State | Risk |
|---|---|---|
| Adding a new module | Easy, follow the pattern | ✅ Low |
| Renaming a model field | Must grep all 8 modules | ⚠️ Medium |
| Testing a single use case in isolation | Hard — services open DB sessions directly | ❌ High |
| Onboarding a new developer | Confusing — three [service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/crm/service.py) files open at once | ⚠️ Medium |
| Adding a REST API layer later (`app/api/` is empty!) | The service layer is untestable without a live DB | ❌ High |
| Performance optimization of one module | Can't isolate — repos are stateless functions, not objects | ⚠️ Medium |

---

## 5. Session Management Anti-Patterns

### 5.1 Multiple Sessions for One Logical Operation

In `academics/service.py` — `schedule_group()` opens **3 separate sessions** for what is conceptually one transaction:

```python
with get_session() as session:  # Session 1: create group + commit
    ...
# Session 2: create sessions in _create_sessions()
_create_sessions(group_id, ...)
with get_session() as session:  # Session 3: refresh group
    group_obj = repo.get_group_by_id(session, group_id)
```

**Risk:** If session 2 fails (e.g., session date validation), the group was already committed by session 1. You now have a group with no sessions — a partially committed operation with no rollback.

This same pattern appears in `crm/service.py` → `register_student()`:
```python
with get_session() as session:  # commit student + link
    ...
siblings = find_siblings(student_id)  # opens a 3rd session
```

### 5.2 `issue_refund` — Session Interleaving

In `finance/service.py`:
```python
with get_session() as db:          # session 1: read original payment
    original_payment = db.get(Payment, payment_id)
    ...
refund_receipt = open_receipt(...)  # session 2 inside open_receipt
with get_session() as db:          # session 3: add refund line + unmark competition fee
    ...
```

Three sessions for one refund operation, with no overarching transaction boundary. A crash between sessions 2 and 3 creates a receipt with no payment line.

---

## 6. What Should Live in a Shared Module

Currently there is **no shared module**. Everything that is shared is either duplicated or imported from unexpected places. A `app/shared/` (or `app/core/`) module should centralize:

### 6.1 Recommended `app/shared/` Contents

```
app/shared/
├── __init__.py
├── types.py            ← Common Literal types (PaymentMethod, EnrollmentStatus, etc.)
├── exceptions.py       ← Custom domain exceptions (NotFoundError, ValidationError, etc.)
├── validators.py       ← Phone validation, date validation, amount validation
├── constants.py        ← WEEKDAYS, status enums, time limits
└── base_repository.py  ← Abstract base with get_by_id, create, update, delete protocol
```

### 6.2 What Currently Is Duplicated or Misplaced

| Item | Currently In | Should Be In |
|---|---|---|
| `validate_phone()` | `crm/service.py` | `shared/validators.py` |
| `WEEKDAYS` list | `academics/service.py` | `shared/constants.py` |
| `_fmt_12h()` time formatter | `academics/service.py` | `shared/utils.py` |
| Status string literals (`'active'`, `'dropped'`, etc.) | Repeated in 5 modules as raw strings | `shared/types.py` |
| `ValueError` as the sole error type | All services | `shared/exceptions.py` with typed errors |
| `dt.utcnow().isoformat()` | Scattered in academics | `shared/utils.py` |

### 6.3 The ValueError Problem

Every service raises `ValueError` for all error classes:

```python
raise ValueError("Student ID not found.")           # not found
raise ValueError("Phone number looks invalid.")      # validation
raise ValueError("Already enrolled in this group.")  # business rule
raise ValueError("Enrollment not found.")            # not found again
```

The UI has to `try/except ValueError` and show a generic error box. There is no way to distinguish a "not found" (which should show 404-style UX) from a "validation failed" (inline form error) from a "business rule violation" (warning dialog).

---

## 7. Specific Code-Level Issues

| # | Location | Issue | Severity |
|---|---|---|---| 
| 1 | `crm/service.py:143` | Bypasses repo layer — raw query in service | 🔴 High |
| 2 | `enrollments/service.py:164` | Same — inline `select()` in service | 🔴 High |
| 3 | `enrollments/service.py:3-4` | Direct cross-module repo imports | 🔴 High |
| 4 | `finance/service.py:124` | Competition domain logic inside finance module | 🔴 High |
| 5 | `academics/service.py:144-158` | `_create_sessions` opens its own session inside an outer service call | 🔴 High |
| 6 | `crm/repository.py:86` | `from sqlalchemy import text` buried mid-file, after functions | 🟡 Medium |
| 7 | `finance/service.py:105` | Hardcoded `method="cash"` default in refund logic | 🟡 Medium |
| 8 | `academics/service.py:155` | `dt.utcnow()` (deprecated in Python 3.12+) — should use `datetime.now(timezone.utc)` | 🟡 Medium |
| 9 | All services | `ValueError` for all error types — no semantic error hierarchy | 🟡 Medium |
| 10 | All repos | No shared base class / protocol — no enforced CRUD contract | 🟡 Medium |
| 11 | `crm/models.py:21` | Forward reference as full string `"app.modules.crm.models.StudentParent"` — fragile if module path changes | 🟢 Low |
| 12 | Connection pool `pool_size=5, max_overflow=5` | Max 10 concurrent connections — fine now, will hit ceiling at ~20 concurrent Streamlit users | 🟢 Low |

---

## 8. What the Architecture Gets Right

> [!TIP]
> Not everything is a problem. These decisions are solid:

- **`get_session()` as context manager with `expire_on_commit=False`** — correct pattern; objects safe post-session
- **Views (`v_enrollment_balance`, `v_siblings`, etc.)** — PostgreSQL-side computation keeps Python dumb; this is the right move
- **`enrollment.level_number` as snapshot** — prevents historical data corruption when a group advances; well-thought-out
- **Receipts as headers + line items** — immutable financial record that supports multi-student payments and refund trails
- **`ADR-9` — Raw SQL for analytics** — correct. ORM cannot express PostgreSQL aggregate filters cleanly
- **`session.flush()` in repos** — getting the auto-incremented ID without committing; showing good transaction awareness
- **`api/` placeholder** — the intention to add a REST API layer later exists; the `app/api/.gitkeep` is a sign the architect knew this day would come

---

## 9. Migration Roadmap

This is a phased recommendation — **not a rewrite**, an incremental improvement.

### Phase A — Shared Foundation (No breaking changes)
1. Create `app/shared/exceptions.py` with `NotFoundError`, `ValidationError`, `BusinessRuleError`
2. Create `app/shared/validators.py` — move `validate_phone()` here
3. Create `app/shared/constants.py` — WEEKDAYS, status literals, time bounds
4. Create `app/shared/types.py` — `EnrollmentStatus = Literal["active","completed","transferred","dropped"]`

### Phase B — Fix Session Anti-Patterns (No interface changes)
5. Rewrite `schedule_group()` to use a single session for group + sessions creation (pass session down)
6. Rewrite `issue_refund()` to use a single session
7. Move `get_parent_students` logic to `crm/repository.py`
8. Move the inline `select(Enrollment)` in `enrollments/service.py:164` to `enrollments/repository.py`

### Phase C — Fix Cross-Module Coupling
9. Replace `from app.modules.crm.repository import get_student_by_id` in `enrollments/service.py` with a call to `crm.service.get_student_by_id()` — services talk to services, repos don't cross boundaries
10. Move competition fee unmarking out of `finance/service.py` — finance should emit an event or call `competition.service.unmark_fee()` instead of directly mutating `TeamMember`

### Phase D — File Renaming (Vertical Slice readiness)
11. Rename files to include domain prefix:
    - `crm/models.py` → `crm/crm_models.py`
    - `crm/repository.py` → `crm/crm_repository.py`
    - etc.
12. OR: Move toward use-case folders per feature (full vertical slice)

---

## 10. Summary Verdict

| Category | Grade | Notes |
|---|---|---|
| Layered architecture intent | ✅ B+ | Pattern is clear and consistently applied |
| File naming | ⚠️ C | All files named identically — poor discoverability |
| DB access strategy | ✅ B | ORM/raw SQL split is intentional; slight inconsistency with `text()` in CRM |
| Session management | ❌ D | Multiple sessions per use case with no overarching transaction; corruption risk |
| Cross-module coupling | ❌ D | Repos imported across module boundaries; finance touches competition internals |
| Error handling | ⚠️ C | Single `ValueError` for all error classes; UI cannot differentiate |
| Shared/common module | ❌ F | Does not exist; logic duplicated across modules |
| Scalability ceiling | ⚠️ C+ | Fine for current scale; will hit maintainability wall around 3-4 more modules |
| Test surface | ❌ D | Services open DB sessions internally — cannot unit test without live DB |
