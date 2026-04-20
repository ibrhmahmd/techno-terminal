# Attendance API Reference

Base path: `/api/v1/attendance`

---

## 🔐 Authentication
All requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### AttendanceStatus
Type: `Literal["present", "absent", "late", "excused"]`

### SessionAttendanceRowDTO
```json
{
  "student_id": 1,
  "status": "present"
}
```

### MarkAttendanceRequest
```json
{
  "entries": [
    { "student_id": 1, "status": "present" },
    { "student_id": 2, "status": "absent" },
    { "student_id": 3, "status": "late" }
  ]
}
```

**Validation Rules:**
- `entries`: Required, minimum 1 item
- `student_id`: Required, positive integer (> 0)
- `status`: Required, must be one of: `"present"`, `"absent"`, `"late"`, `"excused"`
- No duplicate `student_id` values allowed in the list

### MarkAttendanceResponseDTO
```json
{
  "marked": 3,
  "skipped": []
}
```

### EnrollmentAttendanceSummaryDTO
```json
{
  "enrollment_id": 1,
  "sessions_attended": 10,
  "sessions_missed": 2
}
```

### ApiResponse (Envelope)
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

---

## Endpoints

### 1. Get session roster with attendance status
**GET** `/api/v1/attendance/session/{session_id}`

**Path Parameters:**
- `session_id` - integer (required)

**Response (200):** `ApiResponse<list<SessionAttendanceRowDTO>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns attendance status for all enrolled students in session
- Status values: `present`, `absent`, `late`, `excused`
- Includes student_id and current attendance status

---

### 2. Mark / update attendance for a session
**POST** `/api/v1/attendance/session/{session_id}/mark`

**Path Parameters:**
- `session_id` - integer (required)

**Request Body:** `MarkAttendanceRequest`

**Response (200):** `ApiResponse<MarkAttendanceResponseDTO>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Bulk attendance marking for a session
- `entries` is a typed list of `{student_id, status}` objects
- Only provided students are updated (partial update)
- Returns count of marked records and any skipped student_ids
- Validation enforces: positive student_ids, valid statuses, no duplicates, minimum 1 entry

**Example Request:**
```json
{
  "entries": [
    { "student_id": 1, "status": "present" },
    { "student_id": 2, "status": "absent" },
    { "student_id": 3, "status": "late" },
    { "student_id": 4, "status": "excused" }
  ]
}
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "marked": 4,
    "skipped": []
  }
}
```

---

## UI Implementation Notes

### Attendance Grid Pattern
The attendance grid should use **local in-memory state** - not API calls per cell click:

```javascript
// Maintain local state as typed array
const attendanceEntries = [
  { student_id: 1, status: 'present' },
  { student_id: 2, status: 'absent' }
]

// On cell click, update local state only
const handleCellClick = (studentId, status) => {
  const entry = attendanceEntries.find(e => e.student_id === studentId)
  if (entry) {
    entry.status = status
  } else {
    attendanceEntries.push({ student_id: studentId, status })
  }
  // No API call here!
}

// On "Save All" button, fire single POST
const handleSaveAll = () => {
  const payload = {
    entries: attendanceEntries
  }
  api.post(`/attendance/session/${sessionId}/mark`, payload)
}
```

### Balance Badges
Fetch student balance for each row to show debt status:
- `GET /api/v1/finance/balance/student/{student_id}`
- 🟢 Positive balance = Credit (overpayment)
- 🔴 Negative balance = Debt owed
