# Academics API - Attendance Router

Router source: `app/api/routers/attendance.py`  
Mounted prefix: `/api/v1`

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_admin`: admin/system_admin only (all attendance endpoints)

Common auth errors:
- `401 Unauthorized`
- `403 Forbidden`

---

## DTOs and Schemas

### Request DTOs

#### MarkAttendanceRequest
```json
{
  "entries": [
    {"student_id": 12, "status": "present"},
    {"student_id": 15, "status": "absent"},
    {"student_id": 18, "status": "late"}
  ]
}
```

Validation:
- `entries` required array, minimum 1 item
- Each entry requires `student_id` (positive integer) and `status` (see AttendanceStatus)
- No duplicate student IDs allowed in the same request

#### StudentAttendanceItem (individual entry)
```json
{
  "student_id": 12,
  "status": "present"
}
```

Validation:
- `student_id` required, must be > 0
- `status` required, must be one of: `present`, `absent`, `late`, `excused`, `cancelled`

### Response DTOs

#### SessionAttendanceRowDTO (roster item)
```json
{
  "student_id": 12,
  "status": "present"
}
```

#### MarkAttendanceResponseDTO
```json
{
  "marked": 3,
  "skipped": []
}
```

Fields:
- `marked`: Number of attendance records successfully updated
- `skipped`: List of student IDs that were skipped (not found or invalid)

---

## Endpoints

### 1) Get session roster with attendance status
**GET** `/api/v1/attendance/session/{session_id}`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<SessionAttendanceRowDTO>>`

Returns all enrolled students for this session with their current attendance status.

Errors:
- `401`, `403`, `404`

### 2) Mark / update attendance for a session
**POST** `/api/v1/attendance/session/{session_id}/mark`  
Auth: `require_admin`

Path params:
- `session_id` (integer, required)

Request body:
- `MarkAttendanceRequest`

Response:
- `200 OK` -> `ApiResponse<MarkAttendanceResponseDTO>`

Notes:
- Bulk upsert attendance for a session.
- Students not in the list are left unchanged (not automatically set to absent).
- Duplicate student IDs in the request will be rejected with validation error.
- Returns count of marked records and any skipped student IDs.

Example success response:
```json
{
  "success": true,
  "data": {
    "marked": 3,
    "skipped": []
  },
  "message": "Attendance marked: 3 records updated."
}
```

Errors:
- `401`, `403`, `404`, `422`

---

## Attendance Status Values

| Status | Description |
|--------|-------------|
| `present` | Student attended the session |
| `absent` | Student did not attend |
| `late` | Student arrived late |
| `excused` | Student had valid excuse for absence |
| `cancelled` | Session was cancelled (system-set) |

---

## Router Notes

- This router exposes **2 endpoint signatures**.
- All endpoints require admin privileges.
- Attendance is tied to sessions via `session_id`.
- The attendance domain is isolated from academics for clarity and future rate-limiting.
