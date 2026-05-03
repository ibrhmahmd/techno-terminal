# Academics API - Group Lifecycle Router

Router source: `app/api/routers/academics/group_lifecycle.py`

Mounted prefix: `/api/v1`

---

## ⚠️ Deprecation Notice

The following endpoints have been **removed** as of April 2026. Use the consolidated [Group Details Router](group_details.md) endpoints instead:

| Removed Endpoint | Replacement |
|-----------------|-------------|
| `GET /academics/groups/{id}/history` | `GET /academics/groups/{id}/levels/detailed` |
| `GET /academics/groups/{id}/levels` | `GET /academics/groups/{id}/levels/detailed` |
| `GET /academics/groups/{id}/courses/history` | `courses` lookup in `/levels/detailed` |
| `GET /academics/groups/{id}/enrollments/history` | `GET /academics/groups/{id}/enrollments/all` |
| `GET /academics/groups/{id}/levels/analytics` | Analytics merged into `/levels/detailed` |

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

### Response DTOs

#### GroupLevelPublic
```json
{
  "id": 1,
  "group_id": 5,
  "level_number": 2,
  "course_id": 3,
  "course_name": "Robotics Fundamentals",
  "instructor_id": 7,
  "instructor_name": "John Doe",
  "sessions_planned": 12,
  "price_override": 1200.00,
  "status": "active",
  "effective_from": "2026-01-15",
  "effective_to": null,
  "created_at": "2026-01-15T10:30:00"
}
```

Fields:
- `id`: level snapshot ID
- `group_id`: parent group ID
- `level_number`: sequential level number (1, 2, 3...)
- `course_id`, `course_name`: assigned course
- `instructor_id`, `instructor_name`: assigned instructor
- `sessions_planned`: number of sessions planned for this level
- `price_override`: custom price (null means use course default)
- `status`: `active`, `completed`, or `cancelled`
- `effective_from`: when level became active
- `effective_to`: when level ended (null if active)
- `created_at`: snapshot creation timestamp

### Request DTOs

#### CancelLevelInput
```json
{
  "reason": "Insufficient enrollment for this level"
}
```

Fields:
- `reason` (optional): Explanation for cancellation

---

## Endpoints

### 1) Get specific level details
**GET** `/api/v1/academics/groups/{group_id}/levels/{level_number}`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupLevelPublic>` with full course and instructor names

Errors:
- `401`, `403`, `404`

---

### 2) Complete a level and progress to next
**POST** `/api/v1/academics/groups/{group_id}/levels/{level_number}/complete`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Response:
- `200 OK` -> `ApiResponse<dict>` with completed and new level info:
```json
{
  "completed_level": {
    "id": 1,
    "level_number": 1,
    "status": "completed"
  },
  "new_level": {
    "id": 2,
    "level_number": 2,
    "status": "active"
  }
}
```

Errors:
- `401`, `403`, `404`, `400`

Notes:
- Marks current level as `completed` with `effective_to` timestamp
- Creates new level snapshot at `level_number + 1`
- Preserves complete audit trail

---

### 3) Cancel a group level
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

---

### 4) Get enrollment analytics
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

---

### 5) Get instructor history analytics
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

## Router Notes

- The Group Lifecycle router exposes **7 endpoints** for level and history management.
- Immutable level snapshots: Each level progression creates a new `group_levels` record, preserving historical configuration.
- All level endpoints use `GroupLevelPublic` DTO for consistent responses.
- List endpoints support pagination with `skip` and `limit` parameters.
