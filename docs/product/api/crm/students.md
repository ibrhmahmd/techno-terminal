# CRM API - Students Router

Router source: `app/api/routers/crm/students.py`  
Mounted prefix: `/api/v1`  
Router prefix: `/crm`

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

---

## DTOs and Schemas

### Request DTOs

#### RegisterStudentDTO (nested under command)
```json
{
  "full_name": "Omar Mohamed",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "01123456789",
  "notes": "Allergic to peanuts"
}
```

Validation:
- `full_name` required
- other fields optional

#### RegisterStudentCommandDTO
```json
{
  "student_data": {
    "full_name": "Omar Mohamed",
    "date_of_birth": "2010-05-15",
    "gender": "male",
    "phone": "01123456789",
    "notes": "Allergic to peanuts"
  },
  "parent_id": 1,
  "relationship": "son",
  "created_by_user_id": 5
}
```

Validation:
- `student_data` required
- `parent_id`, `relationship`, `created_by_user_id` optional

#### UpdateStudentDTO
```json
{
  "full_name": "Omar Mohamed Updated",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "01123456789",
  "notes": "Updated notes",
  "is_active": true
}
```

Validation:
- all fields optional
- date parsing accepts valid date input

### Response DTOs

#### StudentPublic
```json
{
  "id": 10,
  "full_name": "Omar Mohamed",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "01123456789",
  "is_active": true,
  "notes": "Allergic to peanuts"
}
```

#### StudentListItem
```json
{
  "id": 10,
  "full_name": "Omar Mohamed",
  "phone": "01123456789",
  "is_active": true
}
```

#### ParentPublic (used by student-parents endpoint)
```json
{
  "id": 1,
  "full_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "phone_secondary": "01234567890",
  "email": "ahmed@example.com",
  "relation": "Father",
  "notes": "Primary contact for Omar"
}
```

#### SiblingInfo
```json
{
  "student_id": 11,
  "full_name": "Ali Mohamed",
  "age": 12,
  "parent_id": 1,
  "parent_name": "Ahmed Mohamed"
}
```

#### StudentStatus Enum
```json
"active" | "waiting" | "inactive"
```

#### UpdateStudentStatusDTO
```json
{
  "status": "waiting",
  "notes": "Waiting for Level 2 morning group to open"
}
```

Validation:
- `status` required - must be one of: "active", "waiting", "inactive", " "
- `notes` optional - max 500 characters

#### SetWaitingPriorityDTO
```json
{
  "priority": 1,
  "notes": "VIP student, moved to top of queue"
}
```

Validation:
- `priority` required - integer between 1 and 1000 (1 = highest priority)
- `notes` optional

---

## Endpoints

### 1) List / search students
**GET** `/api/v1/crm/students`  
Auth: `require_any`

Query:
- `q` (optional string, default `""`; search applied only when trimmed length >= 2)
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<StudentListItem>`

Errors:
- `401`, `403`, `422`

### 2) Get student by ID
**GET** `/api/v1/crm/students/{student_id}`  
Auth: `require_any`

Path params:
- `student_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<StudentPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 3) Register a new student
**POST** `/api/v1/crm/students`  
Auth: `require_admin`

Request body:
- `RegisterStudentCommandDTO`

Response:
- `201 Created` -> `ApiResponse<StudentPublic>`

Errors:
- `401`, `403`, `404`, `422`

`404` occurs if `parent_id` is provided but the parent does not exist.

### 4) Update student profile
**PATCH** `/api/v1/crm/students/{student_id}`  
Auth: `require_admin`

Path params:
- `student_id` (integer, required)

Request body:
- `UpdateStudentDTO`

Response:
- `200 OK` -> `ApiResponse<StudentPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 5) Get all parents linked to a student
**GET** `/api/v1/crm/students/{student_id}/parents`  
Auth: `require_any`

Path params:
- `student_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<ParentPublic>>`

Errors:
- `401`, `403`, `404`, `422`

### 6) Get all siblings of a student
**GET** `/api/v1/crm/students/{student_id}/siblings`  
Auth: `require_any`

Path params:
- `student_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<SiblingInfo>>`

Errors:
- `401`, `403`, `404`, `422`

### 7) Delete student (soft delete)
**DELETE** `/api/v1/crm/students/{student_id}`  
Auth: `require_admin`

Path params:
- `student_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<None>`

Errors:
- `401`, `403`, `404`, `422`

Example success response:
```json
{
  "success": true,
  "data": null,
  "message": "Student deleted successfully."
}
```

---

## Status Management Endpoints

### 8) Update student enrollment status
**PATCH** `/api/v1/crm/students/{student_id}/status`
Auth: `require_admin`

Path params:
- `student_id` (integer, required)

Request body:
- `UpdateStudentStatusDTO`

Response:
- `200 OK` -> `ApiResponse<StudentPublic>`

Example request:
```json
{
  "status": "waiting",
  "notes": "Waiting for Level 2 morning group to open"
}
```

Example response:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "full_name": "Omar Mohamed",
    "status": "waiting",
    "waiting_since": "2026-04-05T10:30:00Z",
    "waiting_priority": null,
    "waiting_notes": "Waiting for Level 2 morning group to open",
    "status_history": [
      {
        "timestamp": "2026-04-05T10:30:00Z",
        "changed_by": 5,
        "old_status": "active",
        "new_status": "waiting",
        "notes": "Waiting for Level 2 morning group to open"
      }
    ]
  },
  "message": "Student status updated to waiting"
}
```

Errors:
- `400` - Invalid status value
- `401`, `403`, `404`, `422`

### 9) Toggle student status (active <-> waiting)
**POST** `/api/v1/crm/students/{student_id}/status/toggle`
Auth: `require_admin`

Path params:
- `student_id` (integer, required)

Query params:
- `notes` (optional string) - Audit note for the status change

Response:
- `200 OK` -> `ApiResponse<StudentPublic>`

Example response (toggled to active):
```json
{
  "success": true,
  "data": {
    "id": 123,
    "status": "active",
    "waiting_since": null,
    "waiting_priority": null
  },
  "message": "Student status toggled to active"
}
```

Notes:
- Only supports toggling between `active` and `waiting` statuses
- Returns `400` if called on `inactive` or ` ` students

Errors:
- `400` - Cannot toggle from current status (only active/waiting supported)
- `401`, `403`, `404`, `422`

### 10) Get waiting list
**GET** `/api/v1/crm/students/waiting-list`
Auth: `require_admin`

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `200`, `>= 1`, `<= 1000`)
- `order_by_priority` (optional boolean, default `true`) - Order by priority first, then by wait time

Response:
- `200 OK` -> `ApiResponse<list<StudentPublic>>`

Example response:
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "full_name": "John Doe",
      "status": "waiting",
      "waiting_since": "2026-04-01T00:00:00Z",
      "waiting_priority": 1,
      "waiting_notes": "VIP student, prioritize",
      "date_of_birth": "2015-05-15",
      "gender": "male",
      "phone": "+1234567890"
    }
  ],
  "message": "Retrieved 1 students from waiting list"
}
```

Errors:
- `401`, `403`

### 11) Set waiting list priority
**PATCH** `/api/v1/crm/students/{student_id}/waiting-priority`
Auth: `require_admin`

Path params:
- `student_id` (integer, required)

Request body:
- `SetWaitingPriorityDTO`

Response:
- `200 OK` -> `ApiResponse<StudentPublic>`

Example request:
```json
{
  "priority": 10,
  "notes": "VIP student, moved to top of queue"
}
```

Notes:
- Only works for students with `status = "waiting"`
- Priority 1 = highest priority

Errors:
- `404` - Student not found or not on waiting list
- `401`, `403`, `422`

### 12) Get students by status
**GET** `/api/v1/crm/students/by-status/{status}`
Auth: `require_admin`

Path params:
- `status` (string, required) - One of: "active", "waiting", "inactive", " "

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `200`, `>= 1`, `<= 1000`)

Response:
- `200 OK` -> `ApiResponse<list<StudentPublic>>`

Example: `GET /api/v1/crm/students/by-status/waiting`

Errors:
- `400` - Invalid status value
- `401`, `403`, `422`

### 13) Get student status summary
**GET** `/api/v1/crm/students/status-summary`
Auth: `require_admin`

Response:
- `200 OK` -> `ApiResponse<object>`

Example response:
```json
{
  "success": true,
  "data": {
    "total": 250,
    "active": 200,
    "waiting": 30,
    "inactive": 15
  }
}
```

Errors:
- `401`, `403`

### 14) Get student status history
**GET** `/api/v1/crm/students/{student_id}/status-history`
Auth: `require_admin`

Path params:
- `student_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<object>>`

Example response:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2026-04-05T10:30:00Z",
      "changed_by": 5,
      "old_status": "active",
      "new_status": "waiting",
      "notes": "Waiting for Level 2 morning group to open"
    },
    {
      "timestamp": "2026-04-06T14:20:00Z",
      "changed_by": 3,
      "action": "priority_change",
      "new_priority": 5
    }
  ]
}
```

Errors:
- `404` - Student not found
- `401`, `403`

---

## Router Notes

- This router exposes **14 endpoint signatures** (7 core + 7 status management).
- Student delete is soft-delete behavior in service (`is_active = false`).
- Status history is stored as JSONB in the `status_history` column.
- The `waiting_since` timestamp is automatically set when status changes to `waiting`.
- Siblings endpoint is declared as `SiblingInfo`, but repository output keys differ (`sibling_id`, `sibling_name`), so runtime serialization should be validated in integration tests.
