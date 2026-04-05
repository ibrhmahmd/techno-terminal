# Academics API - Groups Router

Router sources:
- Main Groups: `app/api/routers/academics/groups.py`
- Group Lifecycle: `app/api/routers/academics/group_lifecycle.py`
- Group Competitions: `app/api/routers/academics/group_competitions.py`

Mounted prefix: `/api/v1`

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

#### GroupLevelDTO
```json
{
  "id": 25,
  "group_id": 10,
  "level_number": 1,
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "instructor_id": 7,
  "instructor_name": "Ahmed Hassan",
  "sessions_planned": 16,
  "price_override": 1200.00,
  "status": "active",
  "effective_from": "2026-04-01T10:00:00",
  "effective_to": null,
  "created_at": "2026-04-01T10:00:00"
}
```

#### GroupCompetitionParticipationDTO
```json
{
  "participation_id": 15,
  "competition_id": 3,
  "competition_name": "National Robotics Championship 2026",
  "category_id": 5,
  "category_name": "Junior Level",
  "team_id": 12,
  "team_name": "RoboStars",
  "entered_at": "2026-03-15T09:00:00",
  "left_at": null,
  "is_active": true,
  "final_placement": null,
  "notes": "First time competing"
}
```

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

### 3) Get group by ID
**GET** `/api/v1/academics/groups/{group_id}`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 4) Get enriched group by ID
**GET** `/api/v1/academics/groups/{group_id}/enriched`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<EnrichedGroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 5) Schedule a new group
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

### 6) Update a group
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

### 8) Progress group to next level
**POST** `/api/v1/academics/groups/{group_id}/progress-level`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Increments `level_number`
- Creates new level snapshot in `group_levels` table
- Preserves current level history (sets `effective_to`)
- Updates active enrollments to new level and increases `amount_due`
- Auto-generates regular sessions for the new level

### 9) Soft delete (archive) group
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

### 10) Generate sessions for a specific level
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

## Endpoints - Group Lifecycle

Router source: `app/api/routers/academics/group_lifecycle.py`

### 11) Get full lifecycle history
**GET** `/api/v1/academics/groups/{group_id}/history`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<dict>` containing:
  - group metadata (id, name, created_at)
  - current_level, total_levels, completed_levels
  - levels_timeline: chronological level snapshots
  - course_assignments: course change history
  - enrollment_transitions: student level progressions

Errors:
- `401`, `403`, `404`

### 12) List all level snapshots for a group
**GET** `/api/v1/academics/groups/{group_id}/levels`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `status` (optional): Filter by status (`active`, `completed`, `cancelled`)
- `include_inactive` (optional, default `false`): Include inactive levels

Response:
- `200 OK` -> `ApiResponse<list<GroupLevelDTO>>`

Errors:
- `401`, `403`, `404`

### 13) Get specific level details
**GET** `/api/v1/academics/groups/{group_id}/levels/{level_number}`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupLevelDTO>`

Errors:
- `401`, `403`, `404`

### 14) Complete a level and progress to next
**POST** `/api/v1/academics/groups/{group_id}/levels/{level_number}/complete`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Response:
- `200 OK` -> `ApiResponse<dict>` with completed and new level info

Errors:
- `401`, `403`, `404`, `400`

Notes:
- Marks current level as `completed` with `effective_to` timestamp
- Creates new level snapshot at `level_number + 1`
- Preserves complete audit trail

### 15) Get course assignment history
**GET** `/api/v1/academics/groups/{group_id}/courses/history`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<dict>>` with course assignment records:
  - `course_id`, `assigned_at`, `removed_at`
  - `assigned_by_user_id`, `notes`

Errors:
- `401`, `403`, `404`

### 16) Get enrollment level transitions
**GET** `/api/v1/academics/groups/{group_id}/enrollments/history`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `student_id` (optional): Filter by specific student

Response:
- `200 OK` -> `ApiResponse<list<dict>>` with transition records:
  - `enrollment_id`, `student_id`, `group_level_id`
  - `level_entered_at`, `level_completed_at`, `status`

Errors:
- `401`, `403`, `404`

---

## Endpoints - Group Competitions

Router source: `app/api/routers/academics/group_competitions.py`

### 17) List competition participations for a group
**GET** `/api/v1/academics/groups/{group_id}/competitions`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `is_active` (optional): Filter by active status (true/false/null for all)

Response:
- `200 OK` -> `ApiResponse<list<GroupCompetitionParticipationDTO>>`

Errors:
- `401`, `403`, `404`

### 18) List teams linked to a group
**GET** `/api/v1/academics/groups/{group_id}/teams`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `include_inactive` (optional, default `false`): Include soft-deleted teams

Response:
- `200 OK` -> `ApiResponse<list<dict>>` with team info:
  - `id`, `team_name`, `group_id`, `coach_id`, `created_at`, `is_deleted`

Errors:
- `401`, `403`, `404`

### 19) Link an existing team to a group
**POST** `/api/v1/academics/groups/{group_id}/teams/{team_id}/link`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `team_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<dict>` with linked team info

Errors:
- `401`, `403`, `404`

### 20) Register a team for a competition
**POST** `/api/v1/academics/groups/{group_id}/competitions/{competition_id}/register`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `competition_id` (integer, required)

Query params:
- `team_id` (integer, required): Team to register
- `category_id` (integer, optional): Competition category

Response:
- `200 OK` -> `ApiResponse<dict>` with participation record

Errors:
- `401`, `403`, `404`, `400` (if already registered)

### 21) Mark competition participation as completed
**PATCH** `/api/v1/academics/groups/{group_id}/competitions/{participation_id}/complete`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `participation_id` (integer, required)

Query:
- `final_placement` (integer, optional): Final ranking/placement

Response:
- `200 OK` -> `ApiResponse<dict>` with updated participation

Errors:
- `401`, `403`, `404`

---

## Router Notes

- The main Groups router exposes **10 unique endpoint signatures**.
- The Group Lifecycle router exposes **6 new endpoints** for level and history management.
- The Group Competitions router exposes **5 new endpoints** for competition integration.
- Total: **21 unique endpoint signatures** across all group-related routers.
- Immutable level snapshots: Each level progression creates a new `group_levels` record, preserving historical configuration.
- Soft delete: Teams and groups use soft delete (`is_deleted` flag) to preserve historical data integrity.
