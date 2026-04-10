# Academic Analytics API

Analytics endpoints for academic metrics including enrollments, sessions, attendance, and student progress.

**Base Path:** `/api/v1/analytics`  
**Tag:** `Analytics — Academic`  
**Authentication:** Admin required (`require_admin`)

---

## Endpoints

### 1. Get Dashboard Summary
**GET** `/api/v1/analytics/dashboard/summary`

**Description:** Provides a quick top-level aggregate of the system state including active enrollment count and today's session count.

**Authentication:** Admin required

**Response (200):** `ApiResponse<DashboardSummaryPublic>`

**Example Response:**
```json
{
  "success": true,
  "data": {
    "active_enrollments": 150,
    "today_sessions_count": 8
  },
  "message": "Dashboard summary loaded successfully."
}
```

---

### 2. Get Unpaid Attendees
**GET** `/api/v1/analytics/academics/unpaid-attendees`

**Description:** Returns students attending sessions today who have unpaid balances. Useful for identifying students who need payment reminders before class.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target_date | string (date) | No | Filter date (YYYY-MM-DD). Defaults to today if not provided. |

**Response (200):** `ApiResponse<list<UnpaidAttendeeDTO>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "student_id": 1,
      "student_name": "Omar Mohamed",
      "parent_name": "Ahmed Mohamed",
      "phone_primary": "01123456789",
      "total_balance": -500.0
    }
  ],
  "message": "Unpaid attendees retrieved successfully."
}
```

---

### 3. Get Group Roster
**GET** `/api/v1/analytics/academics/groups/{group_id}/roster`

**Description:** Returns detailed roster for a specific group and level, including attendance statistics and balance for each enrolled student.

**Authentication:** Admin required

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| group_id | integer | Yes | Group ID |

**Query Parameters:**
| Name | Type | Required | Constraints | Description |
|------|------|----------|-------------|-------------|
| level_number | integer | Yes | ge=1 | Level number within the group |

**Response (200):** `ApiResponse<list<GroupRosterRowDTO>>`

**Error Responses:**
- 422 Validation Error - Invalid level_number

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "student_id": 1,
      "student_name": "Omar Mohamed",
      "enrollment_id": 1,
      "enrollment_status": "active",
      "balance": -150.0,
      "sessions_attended": 10,
      "sessions_missed": 2,
      "total_sessions": 12,
      "attendance_pct": 83.3
    }
  ],
  "message": "Group roster retrieved successfully."
}
```

---

### 4. Get Attendance Heatmap
**GET** `/api/v1/analytics/academics/groups/{group_id}/heatmap`

**Description:** Returns attendance heatmap (student x session matrix) for a group, useful for visualizing attendance patterns over time.

**Authentication:** Admin required

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| group_id | integer | Yes | Group ID |

**Query Parameters:**
| Name | Type | Required | Constraints | Description |
|------|------|----------|-------------|-------------|
| level_number | integer | Yes | ge=1 | Level number within the group |

**Response (200):** `ApiResponse<list<AttendanceHeatmapRowDTO>>`

**Error Responses:**
- 422 Validation Error - Invalid level_number

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "student_id": 1,
      "student_name": "Omar Mohamed",
      "session_id": 1,
      "session_number": 1,
      "session_date": "2026-04-03",
      "status": "present"
    }
  ],
  "message": "Attendance heatmap retrieved successfully."
}
```

---

### 5. Get Student Progress
**GET** `/api/v1/analytics/academics/student-progress`

**Description:** Returns student progress analytics including attendance percentage, progress status, and estimated completion date. Can be filtered by student and/or group, or returns all active enrollments if no filters provided.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | No | Filter by specific student ID |
| group_id | integer | No | Filter by specific group ID |

**Response (200):** `ApiResponse<list<StudentProgressDTO>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "student_id": 1,
      "student_name": "Omar Mohamed",
      "course_name": "Robotics Fundamentals",
      "group_name": "Sat 2PM Robotics",
      "current_level": 2,
      "total_sessions": 24,
      "sessions_attended": 20,
      "sessions_missed": 4,
      "attendance_pct": 83.3,
      "progress_status": "on_track",
      "estimated_completion_date": "2026-08-15",
      "enrollment_date": "2026-01-15",
      "last_attendance_date": "2026-04-05"
    }
  ],
  "message": "Student progress retrieved successfully."
}
```

---

### 6. Get Course Completion Rates
**GET** `/api/v1/analytics/academics/course-completion`

**Description:** Returns course completion rates analysis per course, showing how many students started, completed, dropped, or are still in progress.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<CourseCompletionDTO>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "course_id": 1,
      "course_name": "Robotics Fundamentals",
      "started_count": 150,
      "completed_count": 120,
      "dropped_count": 20,
      "in_progress_count": 10,
      "completion_pct": 80.0,
      "avg_days_to_complete": 90.5
    }
  ],
  "message": "Course completion rates retrieved successfully."
}
```

---

## Schemas

### DashboardSummaryPublic
High-level dashboard aggregates for admin view.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| active_enrollments | integer | Yes | Total count of active enrollments |
| today_sessions_count | integer | Yes | Number of sessions scheduled for today |

**Example:**
```json
{
  "active_enrollments": 150,
  "today_sessions_count": 8
}
```

---

### TodaySessionDTO
Detailed session information for today's schedule.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | integer | Yes | Session ID |
| session_date | date | Yes | Session date (YYYY-MM-DD) |
| start_time | time | Yes | Start time |
| end_time | time | Yes | End time |
| session_number | integer | Yes | Session number within level |
| level_number | integer | Yes | Level number |
| group_id | integer | Yes | Group ID |
| course_name | string | Yes | Course name |
| group_name | string | Yes | Group name |
| instructor_name | string | Yes | Instructor name |
| present | integer | Yes | Count of present students |
| absent | integer | Yes | Count of absent students |
| unmarked | integer | Yes | Count of unmarked attendances |
| total_enrolled | integer | Yes | Total enrolled students |

---

### UnpaidAttendeeDTO
Student attending sessions with outstanding balance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student full name |
| parent_name | string | No | Parent/guardian name |
| phone_primary | string | No | Primary phone number |
| total_balance | float | Yes | Outstanding balance (negative = debt) |

**Example:**
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "parent_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "total_balance": -500.0
}
```

---

### GroupRosterRowDTO
Single student entry in group roster with attendance stats.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student full name |
| enrollment_id | integer | Yes | Enrollment ID |
| enrollment_status | string | Yes | Enrollment status (active, dropped, etc.) |
| balance | float | Yes | Current balance |
| sessions_attended | integer | Yes | Number of sessions attended |
| sessions_missed | integer | Yes | Number of sessions missed |
| total_sessions | integer | Yes | Total sessions in level |
| attendance_pct | float | Yes | Attendance percentage |

**Example:**
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "enrollment_id": 1,
  "enrollment_status": "active",
  "balance": -150.0,
  "sessions_attended": 10,
  "sessions_missed": 2,
  "total_sessions": 12,
  "attendance_pct": 83.3
}
```

---

### AttendanceHeatmapRowDTO
Single cell in attendance heatmap (student x session).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student full name |
| session_id | integer | Yes | Session ID |
| session_number | integer | Yes | Sequential session number |
| session_date | date | Yes | Session date |
| status | string | Yes | Attendance status (present, absent, cancelled) |

**Example:**
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "session_id": 1,
  "session_number": 1,
  "session_date": "2026-04-03",
  "status": "present"
}
```

---

### StudentProgressDTO
Student progress analytics for a specific enrollment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student full name |
| course_name | string | Yes | Course name |
| group_name | string | Yes | Group name |
| current_level | integer | Yes | Current level number |
| total_sessions | integer | Yes | Total sessions in level |
| sessions_attended | integer | Yes | Sessions attended count |
| sessions_missed | integer | Yes | Sessions missed count |
| attendance_pct | float | Yes | Attendance percentage |
| progress_status | string | Yes | Status: "on_track", "at_risk", or "behind" |
| estimated_completion_date | date | No | Projected completion date |
| enrollment_date | date | Yes | Enrollment start date |
| last_attendance_date | date | No | Most recent attendance date |

**Example:**
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "course_name": "Robotics Fundamentals",
  "group_name": "Sat 2PM Robotics",
  "current_level": 2,
  "total_sessions": 24,
  "sessions_attended": 20,
  "sessions_missed": 4,
  "attendance_pct": 83.3,
  "progress_status": "on_track",
  "estimated_completion_date": "2026-08-15",
  "enrollment_date": "2026-01-15",
  "last_attendance_date": "2026-04-05"
}
```

---

### CourseCompletionDTO
Course completion rates analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| course_id | integer | Yes | Course ID |
| course_name | string | Yes | Course name |
| started_count | integer | Yes | Students who started the course |
| completed_count | integer | Yes | Students who completed |
| dropped_count | integer | Yes | Students who dropped |
| in_progress_count | integer | Yes | Students currently enrolled |
| completion_pct | float | Yes | Percentage who completed |
| avg_days_to_complete | float | No | Average days to completion |

**Example:**
```json
{
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "started_count": 150,
  "completed_count": 120,
  "dropped_count": 20,
  "in_progress_count": 10,
  "completion_pct": 80.0,
  "avg_days_to_complete": 90.5
}
```

---

## Error Handling

### Common Error Responses

All endpoints may return the following errors:

#### 401 Unauthorized
```json
{
  "success": false,
  "data": null,
  "message": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "success": false,
  "data": null,
  "message": "Admin access required"
}
```

#### 422 Validation Error
```json
{
  "success": false,
  "data": null,
  "message": "Validation error",
  "errors": [
    {
      "loc": ["query", "level_number"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

[← Back to Analytics API Overview](../analytics.md)
