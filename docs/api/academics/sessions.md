# Academics API - Sessions Router

Router source: `app/api/routers/academics/sessions.py`  
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

---

## DTOs and Schemas

### Request DTOs

#### AddExtraSessionInput
```json
{
  "group_id": 10,
  "level_number": 1,
  "extra_date": "2026-04-20",
  "notes": "Make-up class"
}
```

Validation:
- `group_id` required integer (path `group_id` overrides body value at runtime)
- `level_number` required integer
- `extra_date` required date (`YYYY-MM-DD`)

#### UpdateSessionDTO
```json
{
  "session_date": "2026-04-21",
  "start_time": "14:30:00",
  "end_time": "16:30:00",
  "actual_instructor_id": 8,
  "is_substitute": true,
  "notes": "Rescheduled due to holiday",
  "status": "scheduled"
}
```

Validation:
- all fields optional
- date/time fields validated by Pydantic type parsing

#### SubstituteInstructorRequest
```json
{
  "instructor_id": 12
}
```

Validation:
- `instructor_id` required integer

### Response DTOs

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

#### DailyScheduleItem
```json
{
  "session_id": 501,
  "date": "2026-04-11",
  "time_start": "14:00:00",
  "time_end": "16:00:00",
  "status": "scheduled",
  "notes": null,
  "group_id": 10,
  "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
  "level_number": 1,
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "enrolled_count": 12
}
```

---

## Endpoints

### 1) Get daily session schedule
**GET** `/api/v1/academics/sessions/daily-schedule`  
Auth: `require_any`

Query:
- `target_date` (optional date, default: today)

Response:
- `200 OK` -> `ApiResponse<list<DailyScheduleItem>>`

Errors:
- `401`, `403`, `422`

### 2) Add an extra session to a group
**POST** `/api/v1/academics/groups/{group_id}/sessions`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)

Request body:
- `AddExtraSessionInput`

Response:
- `201 Created` -> `ApiResponse<SessionPublic>`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Router overwrites `body.group_id` with path `group_id` before service call.

### 3) Get session details
**GET** `/api/v1/academics/sessions/{session_id}`  
Auth: `require_any`

Path params:
- `session_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<SessionPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 4) Update a session
**PATCH** `/api/v1/academics/sessions/{session_id}`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Request body:
- `UpdateSessionDTO`

Response:
- `200 OK` -> `ApiResponse<SessionPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 5) Delete a session
**DELETE** `/api/v1/academics/sessions/{session_id}`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<None>`

Errors:
- `401`, `403`, `404`, `422`

Example success response:
```json
{
  "success": true,
  "data": null,
  "message": "Session deleted successfully."
}
```

### 6) Cancel a session
**POST** `/api/v1/academics/sessions/{session_id}/cancel`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<SessionPublic>`

Errors:
- `401`, `403`, `404`, `422`

Notes:
- Marks session as "cancelled".
- Updates all attendance records for this session to "cancelled" status.
- Re-numbers remaining sessions (shifts future sessions down by 1).
- Appends a replacement tail session (+7 days from last session).
- Session number is set to 0 (detached from ordering).

### 7) Reactivate a cancelled session
**POST** `/api/v1/academics/sessions/{session_id}/reactivate`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<SessionPublic>`

Errors:
- `401`, `403`, `404`, `400` (if session is not cancelled)

Notes:
- Restores a previously cancelled session to "scheduled" status.
- Removes the replacement session that was created during cancellation.
- Restores session numbering (shifts future sessions up by 1).
- Restores attendance records to "present" status.
- Returns error if session is not in "cancelled" status.

Example success response:
```json
{
  "success": true,
  "data": {
    "id": 501,
    "group_id": 10,
    "level_number": 1,
    "session_number": 2,
    "session_date": "2026-04-11",
    "start_time": "14:00:00",
    "end_time": "16:00:00",
    "status": "scheduled",
    "is_extra_session": false,
    "actual_instructor_id": 7,
    "notes": null
  },
  "message": "Session reactivated successfully."
}
```

### 8) Mark substitute instructor
**POST** `/api/v1/academics/sessions/{session_id}/substitute`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Request body:
- `SubstituteInstructorRequest`

Response:
- `200 OK` -> `ApiResponse<SessionPublic>`

Errors:
- `401`, `403`, `404`, `422`

---

## Router Notes

- This router exposes **8 endpoint signatures**.
- `SubstituteInstructorRequest` uses `instructor_id` (not `substitute_instructor_id`).
