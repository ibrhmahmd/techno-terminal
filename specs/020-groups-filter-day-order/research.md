# Research: Groups Day Order & Search Filter

## Day Ordering Fix — Current Behavior

### The Bug

`get_groups_grouped()` in `app/modules/academics/group/directory/service.py:147` sorts grouped items by `label` alphabetically:

```python
all_items.sort(key=lambda x: x.label)
```

**Current order**: `"Friday", "Monday", "Saturday", "Sunday", "Thursday", "Tuesday", "Wednesday", "Unspecified"`

**Expected order** (Arabic/Islamic week): `"Friday", "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Unspecified"`

### Root Cause

No day-ordering mechanism exists anywhere. Day names are:
- Stored as free `TEXT` in `groups.default_day` (no CHECK constraint, no enum)
- Validated at Pydantic layer via `WeekDay` Literal type in `ScheduleInput.day`
- Listed in `WEEKDAYS` constant (Monday=0…Sunday=6) for date math only
- Duplicated across `academics/constants.py`, `core/schemas.py`, `students_router.py`

### Fix Strategy
1. Add `DAY_ORDER` dict to `app/modules/academics/constants.py`: `{"Friday": 0, "Saturday": 1, "Sunday": 2, "Monday": 3, "Tuesday": 4, "Wednesday": 5, "Thursday": 6, "Unspecified": 7}`
2. In `directory/service.py`, replace `all_items.sort(key=lambda x: x.label)` with `all_items.sort(key=lambda x: DAY_ORDER.get(x.label, 99))`
3. `WEEKDAYS` and `next_weekday()` remain unchanged (use Python Monday=0)

### Files to modify
- `app/modules/academics/constants.py` — add `DAY_ORDER`
- `app/modules/academics/group/directory/service.py` — change sort key in `get_groups_grouped()` (~line 147)

---

## Groups Filter — Reference Pattern

### Student Filter Architecture

**Endpoint**: `GET /crm/students/filter`
**Router**: `app/api/routers/crm/students_router.py` — query params → `StudentFilterDTO`
**Service**: `app/modules/crm/services/search_service.py` — `filter_students(filters: StudentFilterDTO) -> StudentFilterResultDTO`
**Query**: Raw SQL via `sqlalchemy.text()` — CTE-based dynamic WHERE clauses
**Output**: `app/modules/crm/interfaces/dtos/student_filter_result_dto.py`

### Key Pattern Details
- Input: `StudentFilterDTO` with fields `q`, `min_age`, `max_age`, `status`, `gender`, `course_ids`, `group_default_day`, `instructor_name`, `has_unpaid_balance`, `enrollment_date_from`, `enrollment_date_to`, `min_enrollments`, `max_enrollments`, `skip`, `limit`
- Output: `StudentFilterResultDTO` with `students: list[StudentFilterItemDTO]`, `total`, `skip`, `limit`
- Pagination: offset-based, `skip`/`limit`, default `50`, max `200`
- Query: Raw SQL in service layer (NOT repository) with dynamic WHERE construction
- Response: `ApiResponse[StudentFilterResultDTO]` envelope

### Groups Filter Design Proposal

**Endpoint**: `GET /academics/groups/filter`
**Router**: `app/api/routers/academics/group_directory_router.py`
**Slice**: `app/modules/academics/group/directory/` (existing)

**Input DTO** (`GroupFilterDTO`):
- `q: Optional[str]` — free-text search (group name, course name, instructor name)
- `course_ids: Optional[list[int]]` — filter by course
- `day: Optional[list[str]]` — filter by day (accepts full names + abbreviations)
- `instructor_name: Optional[str]` — partial match
- `level_id: Optional[int]` — filter by group level
- `status: Optional[list[str]]` — filter by status (active, inactive, completed)
- `sort_by: Optional[str]` — name (default), day, status
- `sort_order: Optional[str]` — asc (default), desc
- `skip: int = 0`
- `limit: int = 50` (max 200)

**Output DTO** (`GroupFilterResultDTO`):
- `groups: list[EnrichedGroupDTO]` (existing enriched shape)
- `total: int`
- `skip: int`
- `limit: int`

**Service**: `GroupDirectoryService.filter_groups(filters: GroupFilterDTO) -> GroupFilterResultDTO`
- Builds base query from existing `get_enriched_groups()` SQL
- Appends dynamic WHERE clauses based on non-null filter fields
- Appends ORDER BY with `sort_by`/`sort_order`
- Applies pagination (OFFSET/LIMIT in SQL or in-memory)

### Existing Query Base

The enriched groups query lives in `app/modules/academics/group/directory/repository.py`:
- `get_enriched_groups()` — main query joining groups → courses → users (instructor) → group_levels → sessions
- Returns `EnrichedGroupDTO` list
- Currently ordered by `g.id`

### Auth

Use existing `require_admin` dependency from `app/api/dependencies.py` (same as all other groups endpoints).

---

## Key Entities

| Entity | File | Notes |
|--------|------|-------|
| `EnrichedGroupDTO` | `app/modules/academics/group/directory/schemas.py` | Output shape for filter results |
| `GroupFilterDTO` | `app/modules/academics/group/directory/schemas.py` | New — input filter params |
| `GroupFilterResultDTO` | `app/modules/academics/group/directory/schemas.py` | New — output with pagination |
| `DAY_ORDER` | `app/modules/academics/constants.py` | New — day sort mapping |
| `DAY_ABBREV_MAP` | `app/api/routers/crm/students_router.py` | Reference for day abbreviation normalization |
| `GroupDirectoryService` | `app/modules/academics/group/directory/service.py` | Add `filter_groups()` method |
| `GroupDirectoryInterface` | `app/modules/academics/group/directory/interface.py` | Add `filter_groups()` to Protocol |
| `GroupDirectoryRepository` | `app/modules/academics/group/directory/repository.py` | Base enriched query |
