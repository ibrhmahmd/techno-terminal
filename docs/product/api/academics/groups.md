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

#### GroupLevelHistoryResponseDTO
```json
{
  "group_id": 10,
  "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
  "total_levels": 3,
  "completed_levels": 2,
  "active_level": 3,
  "levels": [
    {
      "level_id": 25,
      "level_number": 1,
      "status": "completed",
      "course_id": 1,
      "course_name": "Robotics Fundamentals",
      "instructor_id": 7,
      "instructor_name": "Ahmed Hassan",
      "sessions_planned": 16,
      "sessions_completed": 16,
      "student_count": 12,
      "effective_from": "2026-04-01T10:00:00",
      "effective_to": "2026-06-01T10:00:00"
    }
  ]
}
```

#### GroupEnrollmentHistoryResponseDTO
```json
{
  "group_id": 10,
  "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
  "total_enrollments": 25,
  "active_enrollments": 12,
  "completed_enrollments": 10,
  "dropped_enrollments": 3,
  "enrollments": [
    {
      "enrollment_id": 101,
      "student_id": 55,
      "student_name": "Omar Khaled",
      "student_phone": "+20-123-456-7890",
      "level_number_at_enrollment": 1,
      "enrolled_at": "2026-04-01T10:00:00",
      "status": "active",
      "amount_due": 1200.00,
      "discount_applied": 100.00,
      "payments_made": 600.00,
      "balance_remaining": 500.00
    }
  ]
}
```

#### GroupInstructorHistoryResponseDTO
```json
{
  "group_id": 10,
  "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
  "total_instructors": 2,
  "current_instructor": {
    "instructor_id": 7,
    "instructor_name": "Ahmed Hassan",
    "is_current": true,
    "levels_taught_count": 2,
    "first_assigned_at": "2026-04-01T10:00:00",
    "last_assigned_at": "2026-08-01T10:00:00"
  },
  "instructors": [
    {
      "instructor_id": 7,
      "instructor_name": "Ahmed Hassan",
      "is_current": true,
      "levels_taught_count": 2,
      "first_assigned_at": "2026-04-01T10:00:00",
      "last_assigned_at": "2026-08-01T10:00:00"
    }
  ]
}
```

#### GroupCompetitionHistoryResponseDTO
```json
{
  "group_id": 10,
  "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
  "total_participations": 5,
  "active_participations": 2,
  "completed_participations": 3,
  "competitions": [
    {
      "participation_id": 15,
      "competition_id": 3,
      "competition_name": "National Robotics Championship 2026",
      "team_id": 12,
      "team_name": "RoboStars",
      "category_name": "Junior Level",
      "entered_at": "2026-03-15T09:00:00",
      "left_at": null,
      "is_active": true,
      "final_placement": null,
      "notes": "First time competing"
    }
  ]
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

### 11) Schedule a new level for a group
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

### 12) Progress group to next level
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

### 13) Search groups by name
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

### 14) List groups by type
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

### 15) List groups by course
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

## Endpoints - Group Lifecycle

Router source: `app/api/routers/academics/group_lifecycle.py`

### 16) Get full lifecycle history
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

### 17) List all level snapshots for a group
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

### 18) Get specific level details
**GET** `/api/v1/academics/groups/{group_id}/levels/{level_number}`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupLevelDTO>`

Errors:
- `401`, `403`, `404`

### 19) Complete a level and progress to next
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

### 20) Cancel a group level
**POST** `/api/v1/academics/groups/{group_id}/levels/{level_number}/cancel`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Request body:
- `CancelLevelInput` (optional reason)

Response:
- `200 OK` -> `ApiResponse<dict>` with level_id, level_number, status

Errors:
- `401`, `403`, `404`, `400` (if level already completed)

Notes:
- Cancels a level that hasn't been completed yet.
- Sets status to `cancelled` with timestamp.

### 21) Get course assignment history  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<dict>>` with course assignment records:
  - `course_id`, `assigned_at`, `removed_at`
  - `assigned_by_user_id`, `notes`

Errors:
- `401`, `403`, `404`

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

### 22) Get enrollment level transitions
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

### 23) Get level progression analytics
**GET** `/api/v1/academics/groups/{group_id}/levels/analytics`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupLevelHistoryResponseDTO>`

Notes:
- Returns detailed level history with student counts per level.
- Includes session completion tracking.

### 24) Get enrollment analytics
**GET** `/api/v1/academics/groups/{group_id}/enrollments/analytics`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `status` (optional): Filter by status (active, completed, dropped)
- `skip` (optional, default `0`)
- `limit` (optional, default `100`, max `500`)

Response:
- `200 OK` -> `ApiResponse<GroupEnrollmentHistoryResponseDTO>`

Notes:
- Returns comprehensive enrollment history with payment details.
- Includes student contact information.
- Supports pagination.

### 25) Get instructor history analytics
**GET** `/api/v1/academics/groups/{group_id}/instructors/analytics`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupInstructorHistoryResponseDTO>`

Notes:
- Returns instructor assignment history.
- Shows levels taught count per instructor.
- Identifies current instructor.

Aliases:
- `GET /academics/groups/{group_id}/enrollment-history` → alias for `/enrollments/analytics`
- `GET /academics/groups/{group_id}/instructor-history` → alias for `/instructors/analytics`

---

## Endpoints - Group Competitions

Router source: `app/api/routers/academics/group_competitions.py`

### 26) List competition participations for a group
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

### 27) List teams linked to a group
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

### 28) Link an existing team to a group
**POST** `/api/v1/academics/groups/{group_id}/teams/{team_id}/link`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `team_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<dict>` with linked team info

Errors:
- `401`, `403`, `404`

### 29) Register a team for a competition
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

### 30) Mark competition participation as completed
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

### 31) Withdraw from competition
**DELETE** `/api/v1/academics/groups/{group_id}/competitions/{participation_id}`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `participation_id` (integer, required)

Query:
- `reason` (optional): Reason for withdrawal

Response:
- `200 OK` -> `ApiResponse<dict>` with participation_id, status, withdrawn_at

Errors:
- `401`, `403`, `404`, `400`

Notes:
- Withdraws a group from a competition.
- Sets participation status to `withdrawn`.

### 32) Get competition participation analytics
**GET** `/api/v1/academics/groups/{group_id}/competitions/analytics`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupCompetitionHistoryResponseDTO>`

Notes:
- Returns full competition participation history.
- Includes all competition participations for the group.
- Shows team and category details.
- Includes entry/exit dates and placement results.

---

## Router Notes

- The main Groups router exposes **15 unique endpoint signatures**.
- The Group Lifecycle router exposes **10 new endpoints** for level and history management.
- The Group Competitions router exposes **7 new endpoints** for competition integration.
- Total: **32 unique endpoint signatures** across all group-related routers.
- Immutable level snapshots: Each level progression creates a new `group_levels` record, preserving historical configuration.
- Soft delete: Teams and groups use soft delete (`is_deleted` flag) to preserve historical data integrity.
