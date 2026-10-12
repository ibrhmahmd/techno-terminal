# Academics Module — Refactoring Implementation Plan

> **Source:** Synthesis of two parallel architectural audits (agent + developer), 2026-03-25  
> **Decisions locked:**
> - ✅ Strict per-entity SRP  
> - ✅ All functions return typed Pydantic DTOs (no `dict`)  
> - ✅ `GroupStatus` stays in `shared/constants.py`  
> - ✅ Compatibility adapters in `__init__.py` during migration (no big-bang breakage)  
> - ⏸ Phase 6 (adapter retirement) after all call sites confirmed migrated

---

## Violations Being Resolved

| ID | Violation | Severity | Phase |
|----|-----------|----------|-------|
| A-001 | Service mixes Course + Group + Session + Analytics (SRP) | Critical | 5 |
| A-002 | No service class—functional API, no injectable boundaries | High | 5 |
| A-003 | Repository has Course / Group / Session / Analytics blocks in one file | High | 4 |
| A-004 | Mid-file import of `CourseSession` on line 125 of repo | Medium | 1 |
| A-005 | All DTOs in one `academics_schemas.py` | High | 1 |
| A-006 | `ScheduleGroupInput` imports `_validate_times` from service (DIP violation + circular) | Critical | 2 |
| A-007 | Service functions accept `\| dict` union input | High | 3 |
| A-008 | Service functions return `list[dict]` / `dict \| None` | High | 1 |
| A-009 | Repository returns raw `dict` from SQL queries | High | 1 |
| A-010 | Time constants + WEEKDAYS hard-coded in service | Medium | 1 |
| A-011 | Status/fallback literals hard-coded in repository SQL | Medium | 1 |
| A-012 | Weekday literals duplicated between schema and service | Low | 1 |
| A-013 | Helper functions `_fmt_12h`, `_next_weekday`, `_validate_times`, `_create_sessions_in_session` embedded in service | Medium | 2 |
| A-014 | 6 dead `XxxCreate/XxxRead` classes in model files | Low | 3 |
| A-015 | `update_course`, `update_group`, `update_session`, `UpdateCourseDTO`, `UpdateGroupDTO`, `UpdateSessionDTO` missing from `__init__.py` | Medium | 1 |

---

## Target Directory Structure

```
app/modules/academics/
├── __init__.py                    ← public API facade (adapter exports)
├── constants.py                   ← NEW: all domain constants
│
├── models/                        ← (optional future split, not in this plan)
│   academics_models.py            ← Course, Group table models
│   academics_session_models.py    ← CourseSession table model
│
├── schemas/                       ← NEW sub-folder
│   ├── __init__.py
│   ├── course_schemas.py          ← AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
│   ├── group_schemas.py           ← ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO
│   └── session_schemas.py         ← AddExtraSessionInput, GenerateLevelSessionsInput, UpdateSessionDTO
│
├── helpers/                       ← NEW sub-folder
│   ├── __init__.py
│   ├── time_helpers.py            ← _fmt_12h, _next_weekday, _validate_times
│   └── session_planning.py       ← _create_sessions_in_session
│
├── repositories/                  ← NEW sub-folder
│   ├── __init__.py
│   ├── course_repository.py       ← Course ORM + price update
│   ├── group_repository.py        ← Group ORM + enriched SQL queries
│   ├── session_repository.py      ← CourseSession ORM queries
│   └── course_stats_repository.py ← v_course_stats view queries
│
└── services/                      ← NEW sub-folder
    ├── __init__.py
    ├── course_service.py          ← CourseService class
    ├── group_service.py           ← GroupService class
    └── session_service.py         ← SessionService class
```

---

## Phase 1 — Foundation (No Behavior Change) ✅ Start Here

**Goal:** Create constants, helpers scaffolding, typed read DTOs, fix __init__.py, fix mid-file import.

### 1.1 — [NEW] `academics/constants.py`
```python
from datetime import time

SCHEDULING_START = time(11, 0)      # Replaces _EARLIEST
SCHEDULING_END   = time(21, 0)      # Replaces _LATEST
WEEKDAYS: list[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

GROUP_STATUS_ACTIVE     = "active"   # Replaces "active" literals in repository
GROUP_STATUS_INACTIVE   = "inactive"
GROUP_STATUS_COMPLETED  = "completed"
INSTRUCTOR_PLACEHOLDER  = "Unassigned"  # Replaces COALESCE("Unassigned") label
VIEW_COURSE_STATS       = "v_course_stats"  # Replaces inline SQL view name
```

### 1.2 — [MODIFY] `academics_schemas.py` → split into `schemas/`
Create `schemas/` directory. Move DTOs into entity files:

| New File | Classes It Contains |
|----------|---------------------|
| `schemas/course_schemas.py` | `AddNewCourseInput`, `UpdateCourseDTO`, `CourseStatsDTO` (NEW) |
| `schemas/group_schemas.py` | `ScheduleGroupInput`, `UpdateGroupDTO`, `EnrichedGroupDTO` (NEW) |
| `schemas/session_schemas.py` | `AddExtraSessionInput`, `GenerateLevelSessionsInput`, `UpdateSessionDTO` |
| `schemas/__init__.py` | Re-exports all DTOs for backward compat |

**New typed read DTOs to create:**
```python
class CourseStatsDTO(BaseModel):
    course_id: int; course_name: str
    total_groups: int; active_groups: int
    total_students_ever: int; active_students: int

class EnrichedGroupDTO(BaseModel):
    id: int; group_name: str; course_name: str; instructor_name: str
    level_number: int; default_day: Optional[str]
    default_time_start: Optional[time]; default_time_end: Optional[time]
    max_capacity: Optional[int]; status: str
```

### 1.3 — [MODIFY] `academics_repository.py` — fix mid-file import
Move `from app.modules.academics.academics_session_models import CourseSession` from **line 125** → **line 4** (top of file). Resolves **A-004**.

### 1.4 — [MODIFY] `academia/__init__.py` — add missing exports
Add: `update_course`, `update_group`, `update_session`, `get_all_course_stats`, `get_course_stats`, `UpdateCourseDTO`, `UpdateGroupDTO`, `UpdateSessionDTO`. Resolves **A-015**.

---

## Phase 2 — DIP Fix: Decouple Schema from Service

**Goal:** Break the `schemas.py → service.py` circular import. Resolves **A-006** and **A-013**.

### 2.1 — [NEW] `helpers/time_helpers.py`
```python
from datetime import time, date, timedelta
from app.modules.academics.constants import SCHEDULING_START, SCHEDULING_END, WEEKDAYS

def fmt_12h(t: time) -> str: ...
def next_weekday(from_date: date, day_name: str) -> date: ...
def validate_times(start_time: time, end_time: time) -> None: ...
```

### 2.2 — [NEW] `helpers/session_planning.py`
```python
def create_sessions_in_session(session, group_id, ...) -> list[CourseSession]: ...
```
(Extracted from `academics_service.py` lines 127–159)

### 2.3 — [MODIFY] `schemas/group_schemas.py`
`ScheduleGroupInput.validate_time_window` imports from `helpers.time_helpers`, not from service.

### 2.4 — [MODIFY] `academics_service.py`
Remove `_validate_times`, `_fmt_12h`, `_next_weekday`, `_create_sessions_in_session`; replace with imports from helpers.

---

## Phase 3 — Contract Migration: Remove Dict Inputs + Dead Code

**Goal:** Enforce DTO-only inputs at service boundary. Resolves **A-007** and **A-014**.

### 3.1 — [MODIFY] `academics_service.py`
Remove `| dict` union from `add_new_course` and `schedule_group`:
```python
# Before
def add_new_course(data: AddNewCourseInput | dict) -> Course:
    if isinstance(data, dict):
        data = AddNewCourseInput.model_validate(data)

# After
def add_new_course(data: AddNewCourseInput) -> Course:
```
Call sites (UI forms) must pass the DTO directly. Conversion happens at the UI/API boundary.

### 3.2 — [DELETE] Dead model classes
From `academics_models.py`: Remove `CourseCreate`, `CourseRead`, `GroupCreate`, `GroupRead`.  
From `academics_session_models.py`: Remove `CourseSessionCreate`, `CourseSessionRead`.  
*(If API layer is needed later, these will be regenerated from the proper schema files.)*

---

## Phase 4 — Repository Split

**Goal:** One repository file per entity. Resolves **A-003**, **A-009**, **A-011**.

### New Files

| File | Contains | Lines (approx) |
|------|----------|---------------|
| `repositories/course_repository.py` | `create_course`, `get_course_by_*`, `list_active_courses`, `update_course_price` | ~40 |
| `repositories/group_repository.py` | `create_group`, `list_groups_*`, `get_group_by_id`, `increment_group_level`, `get_enriched_groups*` → now returns `list[EnrichedGroupDTO]` | ~90 |
| `repositories/session_repository.py` | `create_session`, `delete_session`, `list_sessions`, `count_sessions`, `get_max_session_number`, `update_session_instructor` | ~90 |
| `repositories/course_stats_repository.py` | `get_all_course_stats` → returns `list[CourseStatsDTO]`, `get_course_stats` → returns `CourseStatsDTO \| None` | ~40 |
| `repositories/__init__.py` | Re-exports all for backward compat |

**Key rule:** Repository functions that run raw SQL with `text()` must use view/table names from `constants.py`, not inline strings.

---

## Phase 5 — Service Split: Function-Based → Class-Based

**Goal:** Introduce `CourseService`, `GroupService`, `SessionService`. Resolves **A-001**, **A-002**.

### Class Structure

```python
# services/course_service.py
class CourseService:
    def add_new_course(self, data: AddNewCourseInput) -> Course: ...
    def update_course(self, course_id: int, data: UpdateCourseDTO) -> Course: ...
    def update_course_price(self, course_id: int, new_price: float) -> Course: ...
    def get_active_courses(self) -> list[Course]: ...
    def get_all_course_stats(self) -> list[CourseStatsDTO]: ...
    def get_course_stats(self, course_id: int) -> CourseStatsDTO | None: ...

# services/group_service.py
class GroupService:
    def schedule_group(self, data: ScheduleGroupInput) -> tuple[Group, list[CourseSession]]: ...
    def get_groups_by_course(self, course_id: int) -> list[Group]: ...
    def get_all_active_groups(self, include_inactive: bool) -> list[Group]: ...
    def get_all_active_groups_enriched(self) -> list[EnrichedGroupDTO]: ...
    def get_todays_groups_enriched(self) -> list[EnrichedGroupDTO]: ...
    def get_group_by_id(self, group_id: int) -> Group | None: ...
    def update_group(self, group_id: int, data: UpdateGroupDTO) -> Group: ...

# services/session_service.py
class SessionService:
    def generate_level_sessions(self, group_id: int, level: int, start_date: date) -> list[CourseSession]: ...
    def add_extra_session(self, group_id: int, level: int, extra_date: date, notes: str | None) -> CourseSession: ...
    def update_session(self, session_id: int, data: UpdateSessionDTO) -> CourseSession: ...
    def delete_session(self, session_id: int) -> bool: ...
    def mark_substitute_instructor(self, session_id: int, instructor_id: int) -> CourseSession: ...
    def list_group_sessions(self, group_id: int, level: int | None) -> list[CourseSession]: ...
    def check_level_complete(self, group_id: int, level: int) -> bool: ...
    def advance_group_level(self, group_id: int) -> Group: ...
```

### Compatibility Strategy (Critical)
`__init__.py` keeps existing function-level exports as facades:
```python
_course_svc = CourseService()
_group_svc  = GroupService()
_session_svc = SessionService()

add_new_course = _course_svc.add_new_course
schedule_group = _group_svc.schedule_group
# ... etc
```
UI call sites do NOT change. Only internal implementation moves to classes.

---

## Phase 6 — Adapter Retirement (Deferred)

> ⏸ **Execute only after all call sites confirmed to import from service classes directly.**  
> After migration, `__init__.py` becomes a clean re-export of classes only.

---

## File Impact Summary

| Action | Count | Files |
|--------|-------|-------|
| CREATE | 12 | `constants.py`, `schemas/*.py (4)`, `helpers/*.py (3)`, `repositories/*.py (5)`, `services/*.py (4)` |
| MODIFY | 4 | `academics_service.py`, `academics_repository.py`, `academics_models.py`, `academics_session_models.py`, `__init__.py` |
| DELETE | 0 | (files kept until Phase 6; classes deleted within files) |

---

## Acceptance Criteria (Full Completion)

- [ ] `academics_service.py` / `academics_repository.py` / `academics_schemas.py` are empty facades or deleted
- [ ] No function in any academics file returns `dict` or `list[dict]`
- [ ] No function accepts `data: SomeDTO | dict`
- [ ] `ScheduleGroupInput` has zero imports from `academics_service.py`
- [ ] All domain constants live in `academics/constants.py`, not inline
- [ ] `__init__.py` exports every public function and DTO
- [ ] All existing UI call sites work without modification (adapter facades hold)
