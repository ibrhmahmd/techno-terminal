# Academics API - Groups Router

Router source: `app/api/routers/academics/groups_router.py`

Mounted prefix: `/api/v1`

---

## Related Documentation

This file documents the **main Groups Router** (Core CRUD). For related endpoints, see:

- **Group Directory Router**: [group_directory.md](group_directory.md) - Listing, searching, and filtering
- **Group Lifecycle Router**: [group_lifecycle.md](group_lifecycle.md) - Level management, history, analytics
- **Group Competitions Router**: [group_competitions.md](group_competitions.md) - Teams and competition participation

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_any`: any authenticated active user (for `GET` operations)
- `require_admin`: admin/system_admin only (for all mutations)

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

#### ProgressGroupLevelRequest
```json
{
  "price_override": 1200.00,
  "target_level": 3,
  "auto_migrate_enrollments": true,
  "complete_current_level": true,
  "instructor_id": 8,
  "session_start_date": "2026-05-01",
  "course_id": 5,
  "group_name": "Advanced Python - Mon 6PM"
}
```

Validation:
- `price_override` optional (None/0 uses course default price)
- `target_level` optional (defaults to current + 1; must be > current level)
- `auto_migrate_enrollments` optional boolean (default: true)
- `complete_current_level` optional boolean (default: true)
- `instructor_id` optional (must exist in employees table; updates group and new level)
- `session_start_date` optional (YYYY-MM-DD format; overrides default session scheduling)
- `course_id` optional (must exist in courses table; changes group's course and logs to history)
- `group_name` optional (max 255 chars; updates group name if provided)

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
  "status": "active"
}
```

#### ProgressGroupLevelResult
```json
{
  "old_level_number": 1,
  "new_level_number": 2,
  "enrollments_migrated": 12,
  "sessions_created": 8,
  "message": "Group advanced to level 2 with 12 enrollments and 8 sessions."
}
```

#### SessionPublic
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

---

## Endpoints - Groups (Core Router)

### 1) Get group by ID
**GET** `/api/v1/academics/groups/{group_id}`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 2) Schedule a new group
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
- Auto-generates first-level sessions in the same transaction using `course.sessions_per_level`.
- Creates initial level snapshot in `group_levels` table.

### 3) Update a group
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

### 4) Archive a group
**PATCH** `/api/v1/academics/groups/{group_id}/archive`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

Implementation note:
- Group archive is applied by setting internal `status = "completed"`.
- This is used when a group has finished its lifecycle. Enrollments and history are preserved.

### 5) Deactivate a group
**DELETE** `/api/v1/academics/groups/{group_id}`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

Implementation note:
- Group deactivation is applied by setting internal `status = "inactive"`.
- This is a soft delete (suspension) where the group can be reactivated later.

### 6) Progress group to next level
**POST** `/api/v1/academics/groups/{group_id}/progress-level`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Request body:
- `ProgressGroupLevelRequest` (all fields optional)

Response:
- `200 OK` -> `ApiResponse<ProgressGroupLevelResult>`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Completes current level, creates target level, migrates enrollments.
- Can override course, instructor, start date, and group name.

### 7) List sessions for a group
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

### 8) Generate sessions for a specific level
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

---

## Router Notes

- The main Groups router exposes **8 endpoints** focused entirely on core mutations and basic state retrieval.
- Immutable level snapshots: Each level progression creates a new `group_levels` record, preserving historical configuration.
- Separation of concerns: Deactivation (`DELETE`) is distinct from Archiving (`PATCH`).
