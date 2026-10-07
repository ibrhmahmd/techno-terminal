# Data Model: Groups Day Order & Search Filter

## Constants

### `DAY_ORDER` (new — `app/modules/academics/constants.py`)

```python
DAY_ORDER: dict[str, int] = {
    "Friday": 0,
    "Saturday": 1,
    "Sunday": 2,
    "Monday": 3,
    "Tuesday": 4,
    "Wednesday": 5,
    "Thursday": 6,
}
```

Used exclusively for display/sort ordering in `get_groups_grouped()`. Does NOT affect date math (`WEEKDAYS` constant remains unchanged).

---

## Input DTO

### `GroupFilterDTO` (new — `app/modules/academics/group/directory/schemas.py`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | `Optional[str]` | `None` | Free-text search (group name, course name, instructor name, schedule time, notes, enrolled student names) |
| `name` | `Optional[str]` | `None` | Group name exact substring match (separate from `q`) |
| `course_ids` | `Optional[list[int]]` | `None` | Filter by course(s) — current group-course association |
| `course_not` | `Optional[int]` | `None` | Exclude groups ever associated with this course (historical check) |
| `course_name` | `Optional[str]` | `None` | Course name substring match (separate from `q`) |
| `day` | `Optional[list[str]]` | `None` | Filter by day(s) — full names or abbreviations (normalized via DAY_ABBREV_MAP) |
| `instructor_id` | `Optional[int]` | `None` | Current instructor equals this ID |
| `instructor_name` | `Optional[str]` | `None` | Partial instructor name match (separate from `q`) |
| `instructor_has_id` | `Optional[int]` | `None` | Group has EVER had this instructor (historical check) |
| `instructor_not_id` | `Optional[int]` | `None` | Group has NEVER had this instructor (historical check) |
| `level_number` | `Optional[int]` | `None` | Filter by level numeric rank (e.g., 1, 2, 3) |
| `gender` | `Optional[str]` | `None` | Group gender category |
| `age_min` | `Optional[int]` | `None` | Minimum target student age |
| `age_max` | `Optional[int]` | `None` | Maximum target student age |
| `status` | `Optional[list[str]]` | `None` | Filter by group status(es) |
| `price_min` | `Optional[float]` | `None` | Minimum group/course fee |
| `price_max` | `Optional[float]` | `None` | Maximum group/course fee |
| `start_date_from` | `Optional[date]` | `None` | Session start date on or after |
| `start_date_to` | `Optional[date]` | `None` | Session start date on or before |
| `time_from` | `Optional[time]` | `None` | Schedule time on or after |
| `time_to` | `Optional[time]` | `None` | Schedule time on or before |
| `current_session_number` | `Optional[int]` | `None` | Single session number match |
| `session_number_from` | `Optional[int]` | `None` | Session number range start |
| `session_number_to` | `Optional[int]` | `None` | Session number range end |
| `sort_by` | `Optional[Literal["name", "day", "status"]]` | `"name"` | Sort field |
| `sort_order` | `Optional[Literal["asc", "desc"]]` | `"asc"` | Sort direction |
| `skip` | `int` | `0` | Pagination offset |
| `limit` | `int` | `50` | Page size (max 200) |

**Filter logic**:
- Cross-param: AND (all criteria must match)
- Within same param multiple values: OR (e.g., `status=active,inactive` → active OR inactive)
- `q` is a broad OR across all searchable fields
- `name` and `course_name` are separate exact fields (AND with other params, tighter than `q`)

---

## Output DTOs

### `GroupFilterItemDTO` (new — `app/modules/academics/group/directory/schemas.py`)

Reuses fields from existing `EnrichedGroupDTO`. Represents a single group in filter results:

| Field | Type | Source |
|-------|------|--------|
| `id` | `int` | `groups.id` |
| `name` | `str` | `groups.name` |
| `default_day` | `Optional[str]` | `groups.default_day` |
| `status` | `str` | `groups.status` |
| `capacity` | `int` | `groups.capacity` |
| `course_id` | `int` | `groups.course_id` |
| `course_name` | `str` | JOIN `courses.name` |
| `instructor_id` | `int` | `groups.instructor_id` |
| `instructor_name` | `str` | JOIN `users.full_name` |
| `level_id` | `Optional[int]` | `groups.level_id` |
| `level_name` | `Optional[str]` | JOIN `group_levels.name` |
| `level_number` | `Optional[int]` | JOIN `group_levels.level_number` |
| `enrolled_count` | `Optional[int]` | Count of active enrollments |
| `schedule` | `Optional[dict]` | Session schedule info |
| `created_at` | `datetime` | `groups.created_at` |

### `GroupFilterResultDTO` (new — `app/modules/academics/group/directory/schemas.py`)

| Field | Type | Description |
|-------|------|-------------|
| `groups` | `list[GroupFilterItemDTO]` | Filtered groups for current page |
| `total` | `int` | Total matching groups (unpaginated) |
| `skip` | `int` | Offset used |
| `limit` | `int` | Page size used |

---

## Sort Mapping

| `sort_by` value | SQL ORDER BY clause |
|-----------------|---------------------|
| `name` (default) | `g.name ASC` (or DESC) |
| `day` | Use `DAY_ORDER` mapping: `CASE g.default_day WHEN 'Friday' THEN 0 WHEN 'Saturday' THEN 1 ... ELSE 99 END` |
| `status` | `g.status ASC` (or DESC) |
