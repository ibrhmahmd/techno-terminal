# Academic Analytics API

Endpoints related to enrollments, sessions, attendance, and student progress.

---

## Endpoints

### 1. Get Dashboard Summary
`GET /analytics/dashboard/summary`

Provides a high-level aggregate of the system state, including active enrollment counts and today's session details.

**Response Body:** `ApiResponse[DashboardSummaryDTO]`
```json
{
  "active_enrollments": 150,
  "today_sessions_count": 5,
  "sessions": [
    {
      "session_id": 101,
      "session_date": "2026-04-16",
      "start_time": "14:00:00",
      "end_time": "16:00:00",
      "session_number": 3,
      "level_number": 1,
      "group_id": 10,
      "course_name": "Robotics 101",
      "group_name": "Morning Group A",
      "instructor_name": "John Doe",
      "present": 8,
      "absent": 2,
      "unmarked": 0,
      "total_enrolled": 10
    }
  ]
}
```

---

### 2. Get Unpaid Attendees
`GET /analytics/academics/unpaid-attendees`

Returns students attending sessions today (or specified date) who have unpaid balances.

**Query Parameters:**
- `target_date` (optional): Filter by a specific date (YYYY-MM-DD).

**Response Body:** `ApiResponse[list[UnpaidAttendeeDTO]]`
```json
[
  {
    "student_id": 50,
    "student_name": "Jane Smith",
    "parent_name": "Michael Smith",
    "phone_primary": "0123456789",
    "total_balance": -500.0
  }
]
```

---

### 3. Get Group Roster
`GET /analytics/academics/groups/{group_id}/roster`

Returns the full roster for a specific group and level, including attendance stats and financial balance per student.

**Path Parameters:**
- `group_id`: ID of the group.

**Query Parameters:**
- `level_number` (required): Specific level to check.

**Response Body:** `ApiResponse[list[GroupRosterRowDTO]]`
```json
[
  {
    "student_id": 50,
    "student_name": "Jane Smith",
    "enrollment_id": 200,
    "enrollment_status": "active",
    "balance": -500.0,
    "sessions_attended": 5,
    "sessions_missed": 1,
    "total_sessions": 6,
    "attendance_pct": 83.33
  }
]
```

---

### 4. Get Attendance Heatmap
`GET /analytics/academics/groups/{group_id}/heatmap`

Returns a matrix-like list of attendance status for every student across every session in a specific level.

**Path Parameters:**
- `group_id`: ID of the group.

**Query Parameters:**
- `level_number` (required): Specific level to check.

**Response Body:** `ApiResponse[list[AttendanceHeatmapRowDTO]]`
```json
[
  {
    "student_id": 50,
    "student_name": "Jane Smith",
    "session_id": 101,
    "session_number": 1,
    "session_date": "2026-04-01",
    "status": "present"
  }
]
```

---

### 5. Get Student Progress
`GET /analytics/academics/student-progress`

Returns detailed progress status for students, determining if they are "on_track", "at_risk", or "behind" based on attendance and completion.

**Query Parameters:**
- `student_id` (optional): Filter to a single student.
- `group_id` (optional): Filter to a specific group.

**Response Body:** `ApiResponse[list[StudentProgressDTO]]`
```json
[
  {
    "student_id": 50,
    "student_name": "Jane Smith",
    "course_name": "Robotics 101",
    "group_name": "Morning Group A",
    "current_level": 1,
    "total_sessions": 12,
    "sessions_attended": 10,
    "sessions_missed": 2,
    "attendance_pct": 83.33,
    "progress_status": "on_track",
    "estimated_completion_date": "2026-06-01",
    "enrollment_date": "2026-03-15",
    "last_attendance_date": "2026-04-15"
  }
]
```

---

### 6. Get Course Completion Rates
`GET /analytics/academics/course-completion`

Returns aggregated completion, dropout, and in-progress stats for every active course.

**Response Body:** `ApiResponse[list[CourseCompletionDTO]]`
```json
[
  {
    "course_id": 1,
    "course_name": "Robotics 101",
    "started_count": 100,
    "completed_count": 80,
    "dropped_count": 5,
    "in_progress_count": 15,
    "completion_pct": 80.0,
    "avg_days_to_complete": 45.5
  }
]
```
