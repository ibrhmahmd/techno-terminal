# Student Attendance Summary API

Per-enrollment attendance tracking with detailed session records for student profiles.

**Base Path:** `/crm`  
**Authentication:** JWT Bearer token required for all endpoints.

---

## Overview

The attendance summary feature provides detailed attendance records for students, organized by enrollment (group + level combination). Each enrollment includes:

- Complete session history with dates and attendance status
- Aggregated present/absent counts per enrollment
- Group and course information for context

This allows parents and administrators to track attendance patterns across different courses and time periods.

---

## Updated Endpoint

### GET /crm/students/{student_id}/details

Get complete student profile with **per-enrollment attendance summary**.

**Authentication:** `require_any` (any authenticated user)

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Response:** `ApiResponse<StudentWithDetails>`

The response now includes a new `enrollment_attendance` field containing attendance records grouped by enrollment.

```json
{
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "date_of_birth": "2010-01-15",
    "age": 14,
    "gender": "male",
    "phone": "+1234567890",
    "notes": "Student notes",
    "status": "active",
    "is_active": true,
    "school_name": "Springfield Elementary",
    "waiting_since": null,
    "waiting_priority": null,
    "waiting_notes": null,
    "created_at": "2020-01-15T10:00:00Z",
    "updated_at": "2024-01-10T08:30:00Z",
    "primary_parent": {
      "id": 1,
      "full_name": "Parent Name",
      "phone": "+1234567890",
      "email": "parent@example.com",
      "relationship": null
    },
    "current_enrollment": {
      "enrollment_id": 10,
      "group_id": 5,
      "group_name": "Beginners A",
      "course_id": 2,
      "course_name": "Introduction to Programming",
      "level_number": 1,
      "instructor_name": "Prof. Smith"
    },
    "enrollments": [...],
    "balance_summary": {
      "total_due": 1000.00,
      "total_discount": 100.00,
      "total_paid": 500.00,
      "net_balance": 400.00
    },
    "siblings": [...],
    "sessions_attended_count": 45,
    "sessions_absent_count": 3,
    "last_session_attended": "2024-01-08",
    "attendance_stats": {
      "attended": 45,
      "absent": 3,
      "late": 2
    },
    "enrollment_attendance": [
      {
        "enrollment_id": 10,
        "group_id": 5,
        "group_name": "Beginners A",
        "course_name": "Introduction to Programming",
        "level_number": 1,
        "present_count": 8,
        "absent_count": 2,
        "sessions": [
          {
            "session_date": "2024-01-15",
            "status": "present"
          },
          {
            "session_date": "2024-01-22",
            "status": "absent"
          },
          {
            "session_date": "2024-01-29",
            "status": "present"
          },
          {
            "session_date": "2024-02-05",
            "status": "present"
          },
          {
            "session_date": "2024-02-12",
            "status": "late"
          }
        ]
      },
      {
        "enrollment_id": 8,
        "group_id": 3,
        "group_name": "Advanced Robotics",
        "course_name": "Arduino Masterclass",
        "level_number": 2,
        "present_count": 12,
        "absent_count": 1,
        "sessions": [
          {
            "session_date": "2023-09-10",
            "status": "present"
          },
          {
            "session_date": "2023-09-17",
            "status": "present"
          },
          {
            "session_date": "2023-09-24",
            "status": "absent"
          }
        ]
      }
    ]
  }
}
```

**Error Codes:**
- 404: Student not found

---

## Schema Definitions

### StudentWithDetails (Updated)

Extends the existing student profile with per-enrollment attendance data.

**New Field:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| enrollment_attendance | List<StudentEnrollmentAttendanceItem> | Yes | Attendance records grouped by enrollment |

---

### StudentEnrollmentAttendanceItem

Per-enrollment attendance summary with complete session history.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| enrollment_id | integer | Yes | Enrollment ID |
| group_id | integer | Yes | Group ID |
| group_name | string | Yes | Group name |
| course_name | string | Yes | Course name |
| level_number | integer | Yes | Level number within the course |
| present_count | integer | Yes | Count of present/late sessions |
| absent_count | integer | Yes | Count of absent sessions |
| sessions | List<SessionAttendanceItem> | Yes | All session records for this enrollment |

---

### SessionAttendanceItem

Individual session attendance record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_date | date | Yes | Session date (YYYY-MM-DD) |
| status | string | Yes | Attendance status: `present`, `absent`, `cancelled`, or `null` if not marked |

**Status Values:**
- `present` - Student was present
- `late` - Student arrived late (counted as present)
- `absent` - Student was absent
- `cancelled` - Session was cancelled
- `null` - Attendance not yet recorded

---

## Data Organization

### Sort Order

- **Enrollments**: Sorted by enrollment creation date (newest first)
- **Sessions within enrollment**: Sorted by session date (oldest first)

### Count Logic

- **present_count**: Includes both `present` and `late` statuses
- **absent_count**: Only `absent` status
- **Cancelled sessions**: Not counted in either present or absent totals

### Empty Data

If a student has no attendance records:

```json
{
  "enrollment_attendance": [],
  "sessions_attended_count": 0,
  "sessions_absent_count": 0,
  "last_session_attended": null
}
```

---

## Implementation Notes

### Database Query

Attendance data is retrieved using a raw SQL query that:
- Joins `attendance → sessions → enrollments → groups → courses`
- Uses `json_agg` to collect all session records per enrollment
- Groups by enrollment ID for per-enrollment aggregation

### Performance

- Results are cached at the repository level
- JSON aggregation is performed at the database level for efficiency
- Typical response time: < 100ms for students with 50+ sessions

---

## Migration Guide

### For Frontend Developers

**Before:**
```json
{
  "sessions_attended_count": 45,
  "sessions_absent_count": 3,
  "last_session_attended": "2024-01-08"
}
```

**After:**
```json
{
  "sessions_attended_count": 45,
  "sessions_absent_count": 3,
  "last_session_attended": "2024-01-08",
  "enrollment_attendance": [...]
}
```

The existing fields (`sessions_attended_count`, `sessions_absent_count`, `last_session_attended`) remain unchanged and continue to work as before. The new `enrollment_attendance` field provides the detailed breakdown.

### Breaking Changes

None. This is a backward-compatible addition. Existing integrations continue to work without modification.

---

## Related Endpoints

- [GET /crm/students/{student_id}/details](students.md#get-crmstudentsstudent_iddetails) - Full student profile
- [GET /crm/students/{student_id}/siblings](students.md#get-crmstudentsstudent_idsiblings) - Student siblings
- [GET /attendance/sessions/{session_id}](../attendance/sessions.md) - Session attendance management

---

## Changelog

### 2026-04-18

- Added `enrollment_attendance` field to `StudentWithDetails`
- Created `StudentEnrollmentAttendanceItem` schema
- Created `SessionAttendanceItem` schema
- Implemented raw SQL query with json_agg for efficient data retrieval
