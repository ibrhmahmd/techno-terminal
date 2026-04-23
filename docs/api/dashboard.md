# Dashboard API Contract

**Version:** 1.0.0  
**Last Updated:** April 23, 2026  
**Base URL:** `/api/v1`

---

## 1. Overview

The Dashboard API provides administrators with a comprehensive daily overview of all active groups, sessions, and attendance. It implements a **lookup table pattern** to eliminate data duplication—group and instructor metadata appears once in lookup tables, referenced by ID from the scheduled groups array.

### Key Features
- Returns ALL sessions for each group's current level (not limited to target date)
- Groups sorted by `default_time_start` (earliest first)
- Optional attendance grid data via query parameter
- Frontend caching hints via `cache_ttl` and `generated_at` timestamps

---

## 2. Authentication

All dashboard endpoints require **JWT Bearer token authentication** and **admin role authorization**.

### Required Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | `Bearer {jwt_token}` | Yes |
| `Content-Type` | `application/json` | Yes |

### Authorization
- **Role Required:** `admin`
- Non-admin users receive `403 Forbidden`
- Missing/invalid tokens receive `401 Unauthorized`

---

## 3. Endpoint: GET /api/v1/dashboard/daily-overview

Retrieve daily dashboard overview for a specified date.

### 3.1 Request

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `date` | `string` (ISO 8601 Date) | Yes | - | Target date in format `YYYY-MM-DD` |
| `include_attendance` | `boolean` | No | `true` | Include full attendance grid data for each session |

#### Request Example

```bash
curl -X GET "https://api.example.com/api/v1/dashboard/daily-overview?date=2026-04-23&include_attendance=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json"
```

---

### 3.2 Response Schemas

#### Success Response (200 OK)

```typescript
ApiResponse<DashboardDailyOverviewDTO>
```

**Root Response Structure:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `success` | `boolean` | No | Always `true` for successful requests |
| `data` | `DashboardDailyOverviewDTO` | No | Dashboard data payload |
| `message` | `string` | No | Human-readable status message |

---

#### DashboardDailyOverviewDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `date` | `string` (YYYY-MM-DD) | No | The requested target date |
| `generated_at` | `string` (ISO 8601) | No | Server timestamp when data was generated |
| `cache_ttl` | `integer` | No | Recommended cache TTL in seconds (300 = 5 minutes) |
| `groups` | `Record<integer, GroupInfoDTO>` | No | Lookup table: group_id → GroupInfoDTO |
| `instructors` | `Record<integer, InstructorInfoDTO>` | No | Lookup table: instructor_id → InstructorInfoDTO |
| `scheduled_groups` | `ScheduledGroupDTO[]` | No | Array of groups with sessions on target date |
| `summary` | `DashboardSummaryDTO` | No | Aggregate statistics |

---

#### GroupInfoDTO (Lookup Table Entry)

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `int` | No | Unique group identifier |
| `name` | `string` | No | Group name (e.g., "Beginner Group A") |
| `course_name` | `string` | No | Associated course name |
| `instructor_id` | `int` | Yes | Assigned instructor ID (0 if unassigned) |
| `current_level` | `integer` | No | Current level number (default: 1) |
| `default_day` | `string` | Yes | Scheduled day of week (e.g., "Saturday") |
| `default_time_start` | `string` (HH:MM) | Yes | Default start time in 24h format |
| `default_time_end` | `string` (HH:MM) | Yes | Default end time in 24h format |
| `schedule_display` | `string` | No | Formatted schedule (e.g., "Sat 3:00-4:30 PM") |
| `max_capacity` | `integer` | No | Maximum enrollment capacity |
| `student_count` | `integer` | No | Current number of active enrollments |

---

#### InstructorInfoDTO (Lookup Table Entry)

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `int` | No | Unique instructor identifier |
| `name` | `string` | No | Instructor full name (or "Unassigned") |

---

#### ScheduledGroupDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | No | Reference to groups lookup table |
| `today_session` | `TodaySessionDTO` | Yes | Session scheduled for target date |
| `current_level` | `CurrentLevelDTO` | No | All sessions for group's current level |
| `roster` | `StudentRosterDTO[]` | No | Active enrollments with billing status |

---

#### StudentRosterDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `student_id` | `int` | No | Unique student identifier |
| `student_name` | `string` | No | Student full name |
| `gender` | `string` | No | `male` or `female` |
| `billing_status` | `string` | No | `paid` or `due` (calculated from balance) |
| `balance` | `float` | No | Outstanding balance amount (0 if fully paid) |

---

#### TodaySessionDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `session_id` | `int` | No | Unique session identifier |
| `date` | `string` (YYYY-MM-DD) | No | Session date |
| `time_start` | `string` (HH:MM) | No | Start time in 24h format |
| `time_end` | `string` (HH:MM) | No | End time in 24h format |
| `status` | `string` | No | Session status: `scheduled`, `completed`, `cancelled` |

---

#### CurrentLevelDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `level_number` | `integer` | No | Current level number |
| `sessions` | `SessionWithAttendanceDTO[]` | No | All sessions for this level (historical + future) |

---

#### SessionWithAttendanceDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `session_id` | `int` | No | Unique session identifier |
| `session_number` | `integer` | No | Sequential session number within level |
| `date` | `string` (YYYY-MM-DD) | No | Scheduled date |
| `time_start` | `string` (HH:MM) | No | Start time |
| `time_end` | `string` (HH:MM) | No | End time |
| `status` | `string` | No | Session status |
| `is_extra_session` | `boolean` | No | True if extra/make-up session |
| `actual_instructor_id` | `int` | Yes | Substitute instructor ID (0 if same as assigned) |
| `instructor_name` | `string` | Yes | Name of instructor who taught/will teach |
| `is_substitute` | `boolean` | No | True if instructor is a substitute |
| `attendance` | `AttendanceRecordDTO[]` | Yes | Present only if `include_attendance=true` |

---

#### AttendanceRecordDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `student_id` | `int` | No | Unique student identifier |
| `student_name` | `string` | No | Student full name |
| `gender` | `string` | No | `male` or `female` (default: `male`) |
| `status` | `string` | No | Attendance status: `present`, `absent`, `excused`, `late` |

---

#### DashboardSummaryDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `total_groups_today` | `integer` | No | Count of groups with sessions on target date |
| `total_instructors_today` | `integer` | No | Count of unique instructors for today's groups |
| `unique_instructor_ids` | `int[]` | No | Array of instructor IDs scheduled today |

---

### 3.3 Response Examples

#### Success Response (With Attendance)

```json
{
  "success": true,
  "data": {
    "date": "2026-04-23",
    "generated_at": "2026-04-23T08:30:00.000Z",
    "cache_ttl": 300,
    "groups": {
      "101": {
        "id": 101,
        "name": "Beginner Group A",
        "course_name": "Robotics Basics",
        "instructor_id": 55,
        "current_level": 1,
        "default_day": "Saturday",
        "default_time_start": "15:00",
        "default_time_end": "16:30",
        "schedule_display": "Sat 3:00-4:30 PM",
        "max_capacity": 15,
        "student_count": 12
      },
      "102": {
        "id": 102,
        "name": "Advanced Builders",
        "course_name": "Advanced Robotics",
        "instructor_id": 56,
        "current_level": 3,
        "default_day": "Saturday",
        "default_time_start": "17:00",
        "default_time_end": "18:30",
        "schedule_display": "Sat 5:00-6:30 PM",
        "max_capacity": 12,
        "student_count": 10
      }
    },
    "instructors": {
      "55": {
        "id": 55,
        "name": "Ahmed Hassan"
      },
      "56": {
        "id": 56,
        "name": "Sara Mohamed"
      }
    },
    "scheduled_groups": [
      {
        "group_id": 101,
        "today_session": {
          "session_id": 1001,
          "date": "2026-04-23",
          "time_start": "15:00",
          "time_end": "16:30",
          "status": "scheduled"
        },
        "current_level": {
          "level_number": 1,
          "sessions": [
            {
              "session_id": 1001,
              "session_number": 1,
              "date": "2026-04-23",
              "time_start": "15:00",
              "time_end": "16:30",
              "status": "scheduled",
              "is_extra_session": false,
              "actual_instructor_id": 55,
              "instructor_name": "Ahmed Hassan",
              "is_substitute": false,
              "attendance": [
                {
                  "student_id": 2001,
                  "student_name": "Omar Khaled",
                  "gender": "male",
                  "status": "present"
                },
                {
                  "student_id": 2002,
                  "student_name": "Laila Ahmad",
                  "gender": "female",
                  "status": "present"
                }
              ]
            },
            {
              "session_id": 1002,
              "session_number": 2,
              "date": "2026-04-30",
              "time_start": "15:00",
              "time_end": "16:30",
              "status": "scheduled",
              "is_extra_session": false,
              "actual_instructor_id": 55,
              "instructor_name": "Ahmed Hassan",
              "is_substitute": false,
              "attendance": []
            }
          ]
        },
        "roster": [
          {
            "student_id": 2001,
            "student_name": "Omar Khaled",
            "gender": "male",
            "billing_status": "paid",
            "balance": 0.00
          },
          {
            "student_id": 2002,
            "student_name": "Laila Ahmad",
            "gender": "female",
            "billing_status": "due",
            "balance": 150.00
          }
        ]
      },
      {
        "group_id": 102,
        "today_session": {
          "session_id": 2001,
          "date": "2026-04-23",
          "time_start": "17:00",
          "time_end": "18:30",
          "status": "scheduled"
        },
        "current_level": {
          "level_number": 3,
          "sessions": [
            {
              "session_id": 2001,
              "session_number": 5,
              "date": "2026-04-23",
              "time_start": "17:00",
              "time_end": "18:30",
              "status": "scheduled",
              "is_extra_session": false,
              "actual_instructor_id": 56,
              "instructor_name": "Sara Mohamed",
              "is_substitute": false,
              "attendance": [
                {
                  "student_id": 3001,
                  "student_name": "Youssef Ali",
                  "gender": "male",
                  "status": "present"
                }
              ]
            }
          ]
        },
        "roster": [
          {
            "student_id": 3001,
            "student_name": "Youssef Ali",
            "gender": "male",
            "billing_status": "paid",
            "balance": 0.00
          }
        ]
      }
    ],
    "summary": {
      "total_groups_today": 2,
      "total_instructors_today": 2,
      "unique_instructor_ids": [55, 56]
    }
  },
  "message": "Dashboard overview loaded successfully."
}
```

---

#### Empty Response (No Sessions on Date)

```json
{
  "success": true,
  "data": {
    "date": "2026-04-23",
    "generated_at": "2026-04-23T08:30:00.000Z",
    "cache_ttl": 300,
    "groups": {},
    "instructors": {},
    "scheduled_groups": [],
    "summary": {
      "total_groups_today": 0,
      "total_instructors_today": 0,
      "unique_instructor_ids": []
    }
  },
  "message": "Dashboard overview loaded successfully."
}
```

---

#### Success Response (Without Attendance)

```bash
GET /api/v1/dashboard/daily-overview?date=2026-04-23&include_attendance=false
```

Sessions will have `attendance: null` or the field omitted entirely.

---

### 3.4 Error Responses

#### 401 Unauthorized

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid authentication token"
  }
}
```

---

#### 403 Forbidden

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions. Admin role required."
  }
}
```

---

#### 422 Validation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameters",
    "details": [
      {
        "field": "date",
        "message": "Invalid date format. Expected YYYY-MM-DD"
      }
    ]
  }
}
```

---

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to load dashboard overview: [error details]"
  }
}
```

---

## 4. Data Architecture

### 4.1 Lookup Table Pattern

The response uses **lookup tables** to avoid data duplication:

```
Before (Duplicated):
{
  "scheduled_groups": [
    { "group_id": "101", "group_name": "Group A", "instructor_name": "Ahmed" },
    { "group_id": "102", "group_name": "Group B", "instructor_name": "Ahmed" }
  ]
}

After (Deduplicated):
{
  "groups": {
    "101": { "name": "Group A" },
    "102": { "name": "Group B" }
  },
  "instructors": {
    "55": { "name": "Ahmed" }
  },
  "scheduled_groups": [
    { "group_id": "101", ... },
    { "group_id": "102", ... }
  ]
}
```

### 4.2 4-Query Strategy

The backend implements an efficient 4-query fetch pattern:

1. **Query 1:** Get groups with sessions on target date
2. **Query 2:** Get group metadata and instructor info (batch)
3. **Query 3:** Get ALL sessions for current levels (batch)
4. **Query 4:** Get attendance records (batch, optional)

---

## 5. Implementation Notes

### 5.1 Filtering Rules
- Only groups with `status = 'active'` are included
- Only sessions for the group's `current_level` are returned
- Groups are sorted by `default_time_start` ASC, then `name` ASC

### 5.2 Instructor Resolution
- Primary instructor sourced from `employees` table
- Substitute instructors tracked at session level via `actual_instructor_id`

### 5.3 Caching Recommendations
- **Client-side:** Use `cache_ttl` (300 seconds) as guideline
- **No server-side caching:** Fresh data fetched per request
- `generated_at` timestamp for cache invalidation logic

---

## 6. Changelog

### v1.0.0 (2026-04-23)
- Initial implementation
- Added `GET /api/v1/dashboard/daily-overview` endpoint
- Implemented lookup table pattern for groups and instructors
- Added optional attendance data via `include_attendance` parameter
