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
  "session_id": "integer (required)",
  "student_statuses": {
    "1": "present",
    "2": "absent",
    "3": "late"
  },
  "marked_by_user_id": "integer (optional)"
}
```

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
- `student_statuses` is a dict mapping student_id → status
- Only provided students are updated (partial update)
- Returns count of marked records and any skipped student_ids

**Example Request:**
```json
{
  "session_id": 1,
  "student_statuses": {
    "1": "present",
    "2": "absent",
    "3": "late",
    "4": "excused"
  },
  "marked_by_user_id": 1
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
// Maintain local state map
const attendanceMap = {
  [studentId]: status
}

// On cell click, update local state only
const handleCellClick = (studentId, status) => {
  attendanceMap[studentId] = status
  // No API call here!
}

// On "Save All" button, fire single POST
const handleSaveAll = () => {
  const payload = {
    session_id: currentSessionId,
    student_statuses: attendanceMap,
    marked_by_user_id: currentUserId
  }
  api.post(`/attendance/session/${sessionId}/mark`, payload)
}
```

### Balance Badges
Fetch student balance for each row to show debt status:
- `GET /api/v1/finance/balance/student/{student_id}`
- 🟢 Positive balance = Credit (overpayment)
- 🔴 Negative balance = Debt owed
