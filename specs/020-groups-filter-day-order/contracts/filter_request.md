# API Contract: GET /academics/groups/filter

## Request

```
GET /api/v1/academics/groups/filter?q=robot&course_ids=1,3&course_not=5&day=Saturday&instructor_id=2&status=active&level_number=2&gender=male&age_min=8&age_max=12&price_min=0&price_max=500&current_session_number=3&sort_by=name&sort_order=asc&skip=0&limit=50
```

**Headers**: `Authorization: Bearer <jwt>`

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | No | — | Free-text search across name, course, instructor, time, notes, student names |
| `name` | string | No | — | Group name exact substring match |
| `course_ids` | comma-separated ints | No | — | Filter by current course(s) |
| `course_not` | int | No | — | Exclude groups ever associated with this course |
| `course_name` | string | No | — | Course name substring match |
| `day` | comma-separated strings | No | — | Filter by day(s) — full name or abbreviation (Fri/Sat/Sun/Mon/Tue/Wed/Thu) |
| `instructor_id` | int | No | — | Current instructor equals this ID |
| `instructor_name` | string | No | — | Partial instructor name match |
| `instructor_has_id` | int | No | — | Group has EVER had this instructor |
| `instructor_not_id` | int | No | — | Group has NEVER had this instructor |
| `level_number` | int | No | — | Filter by level numeric rank (1, 2, 3…) |
| `gender` | string | No | — | Group gender category |
| `age_min` | int | No | — | Minimum target student age |
| `age_max` | int | No | — | Maximum target student age |
| `status` | comma-separated strings | No | — | Filter by status(es): active, inactive, completed |
| `price_min` | float | No | — | Minimum group/course fee |
| `price_max` | float | No | — | Maximum group/course fee |
| `start_date_from` | date (YYYY-MM-DD) | No | — | Session start on or after |
| `start_date_to` | date (YYYY-MM-DD) | No | — | Session start on or before |
| `time_from` | time (HH:MM) | No | — | Schedule time on or after |
| `time_to` | time (HH:MM) | No | — | Schedule time on or before |
| `current_session_number` | int | No | — | Groups currently at this session number |
| `session_number_from` | int | No | — | Session number range start |
| `session_number_to` | int | No | — | Session number range end |
| `sort_by` | string | No | `name` | Sort field: name, day, status |
| `sort_order` | string | No | `asc` | Sort direction: asc, desc |
| `skip` | int | No | `0` | Pagination offset |
| `limit` | int | No | `50` | Page size (max 200) |

### Day Name Normalization

Accepts both full names and abbreviations, matching the existing `DAY_ABBREV_MAP`:

| Abbreviation | Full Name |
|-------------|-----------|
| mon | Monday |
| tue | Tuesday |
| wed | Wednesday |
| thu, thurs | Thursday |
| fri | Friday |
| sat | Saturday |
| sun | Sunday |

### Filter Logic

- **AND across parameters**: all non-null params must match
- **OR within multi-value params**: `course_ids=1,3` → course 1 OR course 3
- **`q` is broad OR** across all searchable fields (name, course name, instructor name, schedule time, notes, student names)
- **`name` and `course_name`** are separate AND-criteria exact matches (tighter than including them in `q`)
