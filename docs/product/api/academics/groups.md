# Academics API - Groups Router

Router source: `app/api/routers/academics/groups.py`

Mounted prefix: `/api/v1`

---

## Related Documentation

This file documents the **main Groups Router**. For related endpoints, see:

- **Group Lifecycle Router**: [group_lifecycle.md](group_lifecycle.md) - Level management, history, analytics
- **Group Competitions Router**: [group_competitions.md](group_competitions.md) - Teams and competition participation

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

Common auth errors:
- `401 Unauthorized`
- `403 Forbidden`

---

## DTOs and Schemas

### Request DTOs

#### ScheduleGroupInput
```json
{
  "course_id": 1,
  "instructor_id": 7,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "default_time_end": "16:00:00",
  "notes": "Weekend batch",
  "max_capacity": 15
}
```

Validation:
- `course_id` required
- `instructor_id` required
- `default_day` required, one of `Monday..Sunday`
- `default_time_start` and `default_time_end` required (`HH:MM:SS`)
- time window must be between `11:00` and `21:00`
- `default_time_end` must be after `default_time_start`
- `max_capacity` optional, default `15`

#### UpdateGroupDTO
```json
{
  "name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "level_number": 2,
  "max_capacity": 18,
  "instructor_id": 8,
  "default_day": "Saturday",
  "default_time_start": "14:30:00",
  "default_time_end": "16:30:00",
  "notes": "Rescheduled",
  "status": "active"
}
```

Validation:
- all fields optional
- no extra custom validator is applied in this DTO

#### GenerateLevelSessionsRequest
```json
{
  "level_number": 2,
  "start_date": "2026-05-01"
}
```

Validation:
- `level_number` required (integer)
- `start_date` optional (`YYYY-MM-DD`), defaults to current date if omitted

#### ScheduleGroupLevelRequest
```json
{
  "level_number": 2,
  "instructor_id": 8,
  "price_override": 1200.00,
  "start_date": "2026-05-01"
}
```

Validation:
- `level_number` required integer
- `instructor_id` optional (override group's default instructor)
- `price_override` optional (None/0 uses course default price)
- `start_date` optional date, defaults to next weekday from today

#### ProgressGroupLevelRequest
```json
{
  "price_override": 1200.00
}
```

Validation:
- `price_override` optional (None/0 uses course default price)

#### CancelLevelInput
```json
{
  "reason": "Low enrollment"
}
```

Validation:
- `reason` optional string, max 500 characters

### Response DTOs

#### GroupPublic
```json
{
  "id": 10,
  "name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "instructor_id": 7,
  "level_number": 1,
  "max_capacity": 15,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "default_time_end": "16:00:00",
  "is_active": true
}
```

#### GroupListItem
```json
{
  "id": 10,
  "name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "level_number": 1,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "is_active": true
}
```

#### EnrichedGroupPublic
```json
{
  "id": 10,
  "name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "instructor_id": 7,
  "instructor_name": "Ahmed Hassan",
  "level_number": 1,
  "max_capacity": 15,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "default_time_end": "16:00:00",
  "is_active": true
}
```

#### SessionPublic (for session list/generation responses)
```json
{
  "id": 501,
  "group_id": 10,
  "level_number": 1,
  "session_number": 1,
  "session_date": "2026-04-11",
  "start_time": "14:00:00",
  "end_time": "16:00:00",
  "status": "scheduled",
  "is_extra_session": false,
  "actual_instructor_id": 7,
  "notes": null
}
```

#### GroupedGroupsResponse
```json
{
  "groups": [
    {
      "key": "saturday",
      "label": "Saturday",
      "count": 5,
      "groups": [
        {
          "id": 10,
          "name": "Saturday 2:00 PM - Robotics Fundamentals",
          "course_name": "Robotics Fundamentals",
          "instructor_name": "Ahmed Hassan",
          "...": "..."
        }
      ]
    }
  ],
  "total": 7,
  "group_by": "day"
}
```

Fields:
- `groups`: array of grouped items
- `key`: grouping key (e.g., "saturday", "1", "active")
- `label`: display label (e.g., "Saturday", "Robotics Fundamentals", "Active")
- `count`: number of groups in this category
- `total`: total number of groups across all categories
- `group_by`: the field used for grouping

---

## Endpoints - Groups (Main Router)

### 1) List all active groups
**GET** `/api/v1/academics/groups`  
Auth: `require_any`

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `422`

### 2) Get all active enriched groups
**GET** `/api/v1/academics/groups/enriched`  
Auth: `require_any`

Response:
- `200 OK` -> `ApiResponse<list<EnrichedGroupPublic>>`

Errors:
- `401`, `403`

### 3) Get groups grouped by field
**GET** `/api/v1/academics/groups/grouped`  
Auth: `require_any`

Query:
- `group_by` (required): Field to group by - one of `day`, `course`, `instructor`, `status`
- `skip` (optional, default `0`, `>= 0`): Pagination offset
- `limit` (optional, default `50`, `>= 1`, `<= 200`): Page size
- `search` (optional): Search term to filter groups by name/course/instructor

Response:
- `200 OK` -> `ApiResponse<GroupedGroupsResponse>`

Errors:
- `401`, `403`, `422`

Example Response:
```json
{
  "success": true,
  "data": {
    "groups": [
      {
        "key": "saturday",
        "label": "Saturday",
        "count": 5,
        "groups": [ /* EnrichedGroupPublic array */ ]
      },
      {
        "key": "sunday",
        "label": "Sunday",
        "count": 3,
        "groups": [ /* EnrichedGroupPublic array */ ]
      }
    ],
    "total": 2,
    "group_by": "day"
  }
}
```

Notes:
- Groups are organized by the specified field for easier navigation.
- Supports pagination at the group level.
- Search filters groups before grouping.

### 4) Get groups by course
**GET** `/api/v1/academics/groups/course/{course_id}`  
Auth: `require_any`

Path params:
- `course_id` (integer, required)

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `404`, `422`

### 4) Get archived groups (paginated)
**GET** `/api/v1/academics/groups/archived`  
Auth: `require_any`

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `422`

### 5) Get group by ID
**GET** `/api/v1/academics/groups/{group_id}`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 6) Get enriched group by ID
**GET** `/api/v1/academics/groups/{group_id}/enriched`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<EnrichedGroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 7) Schedule a new group
**POST** `/api/v1/academics/groups`  
Auth: `require_admin`

Request body:
- `ScheduleGroupInput`

Response:
- `201 Created` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Auto-generates group name from weekday/time/course name.
- Auto-generates first-level sessions in the same transaction.
- Creates initial level snapshot in `group_levels` table.

### 8) Update a group
**PATCH** `/api/v1/academics/groups/{group_id}`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Request body:
- `UpdateGroupDTO`

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 9) List sessions for a group
**GET** `/api/v1/academics/groups/{group_id}/sessions`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `level` (optional integer, filter by level number)

Response:
- `200 OK` -> `ApiResponse<list<SessionPublic>>`

Errors:
- `401`, `403`, `422`

### 10) Soft delete (archive) group
**DELETE** `/api/v1/academics/groups/{group_id}`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

Implementation note:
- Group archive is applied by setting internal `status = "inactive"`.
- All level snapshots are preserved in history.

### 11) Generate sessions for a specific level
**POST** `/api/v1/academics/groups/{group_id}/generate-sessions`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Request body:
- `GenerateLevelSessionsRequest`

Response:
- `201 Created` -> `ApiResponse<list<SessionPublic>>`

Errors:
- `401`, `403`, `404`, `409`, `422`

`409` occurs when sessions already exist for that group level.

### 12) Schedule a new level for a group
**POST** `/api/v1/academics/groups/{group_id}/schedule-level`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Request body:
- `ScheduleGroupLevelRequest`

Response:
- `201 Created` -> `ApiResponse<dict>`:
  - `level_id`, `level_number`, `group_id`
  - `sessions_created`: count
  - `sessions`: array of `{id, session_number, date}`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Creates GroupLevel record and generates sessions for the new level.
- Uses group's default instructor if `instructor_id` not provided.

### 13) Progress group to next level
**POST** `/api/v1/academics/groups/{group_id}/progress-level`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Request body:
- `ProgressGroupLevelRequest` (price_override optional)

Response:
- `200 OK` -> `ApiResponse<ProgressGroupLevelResult>`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Completes current level, creates new level, migrates enrollments.

### 14) Search groups by name
**GET** `/api/v1/academics/groups/search`  
Auth: `require_any`

Query:
- `query` (required, min length 2): Search string
- `status` (optional): Filter by status
- `skip` (optional, default `0`)
- `limit` (optional, default `20`, max `100`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `422`

### 15) List groups by type
**GET** `/api/v1/academics/groups/by-type/{group_type}`  
Auth: `require_any`

Path params:
- `group_type` (string, required)

Query:
- `status` (optional): Filter by status
- `skip` (optional, default `0`)
- `limit` (optional, default `50`, max `200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `404`

### 16) List groups by course
**GET** `/api/v1/academics/groups/by-course/{course_id}`  
Auth: `require_any`

Path params:
- `course_id` (integer, required, > 0)

Query:
- `include_inactive` (optional, default `false`)
- `level_number` (optional, > 0): Filter by level
- `skip` (optional, default `0`)
- `limit` (optional, default `50`, max `200`)

Response:
- `200 OK` -> `PaginatedResponse<EnrichedGroupPublic>`

Errors:
- `401`, `403`, `404`

---

## Related Documentation

For group lifecycle and competition endpoints, see:
- **[Group Lifecycle Router](group_lifecycle.md)** - Level management, history, and analytics
- **[Group Competitions Router](group_competitions.md)** - Team and competition integration

---

## Router Notes

- The main Groups router exposes **17 unique endpoint signatures** (including the new `/grouped` endpoint).
- All list endpoints support pagination with `skip` and `limit` parameters.
- Immutable level snapshots: Each level progression creates a new `group_levels` record, preserving historical configuration.
- Soft delete: Groups use soft delete (status change) to preserve historical data integrity.

## See Also

- **[Group Lifecycle Router](group_lifecycle.md)** - Level management, history, and analytics endpoints
- **[Group Competitions Router](group_competitions.md)** - Team and competition integration endpoints
