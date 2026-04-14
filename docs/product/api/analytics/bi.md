# Business Intelligence (BI) Analytics API

Advanced analytics endpoints for business intelligence: trends, retention, performance metrics, and risk analysis.

**Base Path:** `/api/v1/analytics`  
**Tag:** `Analytics — BI`  
**Authentication:** Admin required (`require_admin`)

---

## Endpoints

### 1. Get Enrollment Trend
**GET** `/api/v1/analytics/bi/enrollment-trend`

**Description:** Returns daily new enrollment counts over time for trend analysis.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| cutoff | string (date) | No | Start date for trend analysis (YYYY-MM-DD). Defaults to 90 days ago. |

**Response (200):** `ApiResponse<list<EnrollmentTrendItem>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "day": "2026-04-01",
      "new_enrollments": 5
    },
    {
      "day": "2026-04-02",
      "new_enrollments": 3
    }
  ],
  "message": "Enrollment trend retrieved successfully."
}
```

---

### 2. Get Retention Metrics
**GET** `/api/v1/analytics/bi/retention`

**Description:** Returns enrollment retention and dropout rates per course.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<RetentionMetricsResponse>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "course_name": "Robotics Fundamentals",
      "active_count": 45,
      "dropped_count": 5,
      "total_enrollments": 50
    }
  ],
  "message": "Retention metrics retrieved successfully."
}
```

---

### 3. Get Instructor Performance
**GET** `/api/v1/analytics/bi/instructor-performance`

**Description:** Returns group and active student counts per instructor.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<InstructorPerformanceItem>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "instructor_name": "Ahmed Hassan",
      "active_groups": 4,
      "active_students": 32
    }
  ],
  "message": "Instructor performance retrieved successfully."
}
```

---

### 4. Get Level Retention Funnel
**GET** `/api/v1/analytics/bi/retention-funnel`

**Description:** Returns student counts per course/level showing progression funnel (how many students reach each level).

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<LevelRetentionFunnelItem>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "course_name": "Robotics Fundamentals",
      "level_number": 1,
      "student_count": 50
    },
    {
      "course_name": "Robotics Fundamentals",
      "level_number": 2,
      "student_count": 42
    }
  ],
  "message": "Level retention funnel retrieved successfully."
}
```

---

### 5. Get Instructor Value Matrix
**GET** `/api/v1/analytics/bi/instructor-value`

**Description:** Returns revenue and attendance correlation per instructor to identify high-value instructors.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<InstructorValueMatrixItem>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "instructor_name": "Ahmed Hassan",
      "total_revenue": 75000.0,
      "avg_attendance_pct": 92.5
    }
  ],
  "message": "Instructor value matrix retrieved successfully."
}
```

---

### 6. Get Schedule Utilization
**GET** `/api/v1/analytics/bi/schedule-utilization`

**Description:** Returns schedule slot utilization percentages to identify underutilized or overbooked time slots.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<ScheduleUtilizationItem>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "day": "Saturday",
      "time_start": "14:00",
      "total_enrolled": 45,
      "total_capacity": 60,
      "utilization_pct": 75.0
    }
  ],
  "message": "Schedule utilization retrieved successfully."
}
```

---

### 7. Get Flight-Risk Students
**GET** `/api/v1/analytics/bi/flight-risk`

**Description:** Returns students likely to drop out based on attendance patterns and outstanding debt.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<FlightRiskStudentItem>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "student_name": "Omar Mohamed",
      "course_name": "Robotics Fundamentals",
      "amount_owed": -500.0,
      "sessions_missed": 3
    }
  ],
  "message": "Flight-risk students retrieved successfully."
}
```

---

### 8. Get User Engagement
**GET** `/api/v1/analytics/bi/user-engagement`

**Description:** Returns daily user engagement metrics including active users, session duration, and feature usage patterns.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| days | integer | No | 30 | ge=1, le=90 | Number of days to analyze |

**Response (200):** `ApiResponse<list<UserEngagementItem>>`

**Error Responses:**
- 422 Validation Error - days must be between 1 and 90

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-04-05",
      "daily_active_users": 25,
      "total_sessions": 85,
      "avg_session_duration_minutes": 45.5,
      "feature_usage": {
        "attendance_marking": 45,
        "student_search": 30,
        "receipt_creation": 10
      }
    }
  ],
  "message": "User engagement metrics retrieved successfully."
}
```

---

### 9. Get Retention Analysis (Cohort)
**GET** `/api/v1/analytics/bi/retention-analysis`

**Description:** Returns cohort-based retention analysis showing how student cohorts retain over time.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| months | integer | No | 6 | ge=1, le=12 | Number of months for cohort analysis |

**Response (200):** `ApiResponse<list<RetentionCohortItem>>`

**Error Responses:**
- 422 Validation Error - months must be between 1 and 12

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "cohort_month": "2026-01",
      "initial_enrollments": 50,
      "retention_by_month": {
        "month_1": 48,
        "month_2": 45,
        "month_3": 42
      },
      "retention_rates": {
        "month_1": 96.0,
        "month_2": 90.0,
        "month_3": 84.0
      }
    }
  ],
  "message": "Retention analysis retrieved successfully."
}
```

---

## Schemas

### EnrollmentTrendItem
Daily enrollment count for trend analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| day | date | Yes | Date (YYYY-MM-DD) |
| new_enrollments | integer | Yes | Count of new enrollments that day |

**Example:**
```json
{
  "day": "2026-04-01",
  "new_enrollments": 5
}
```

---

### RetentionMetricsResponse
Retention metrics per course.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| course_name | string | Yes | Course name |
| active_count | integer | Yes | Currently active students |
| dropped_count | integer | Yes | Students who dropped |
| total_enrollments | integer | Yes | Total enrollment count |

**Example:**
```json
{
  "course_name": "Robotics Fundamentals",
  "active_count": 45,
  "dropped_count": 5,
  "total_enrollments": 50
}
```

---

### InstructorPerformanceItem
Performance metrics per instructor.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| instructor_name | string | Yes | Instructor full name |
| active_groups | integer | Yes | Number of groups they teach |
| active_students | integer | Yes | Total students across all their groups |

**Example:**
```json
{
  "instructor_name": "Ahmed Hassan",
  "active_groups": 4,
  "active_students": 32
}
```

---

### LevelRetentionFunnelItem
Student count per level showing progression funnel.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| course_name | string | Yes | Course name |
| level_number | integer | Yes | Level number |
| student_count | integer | Yes | Students at this level |

**Example:**
```json
{
  "course_name": "Robotics Fundamentals",
  "level_number": 1,
  "student_count": 50
}
```

---

### InstructorValueMatrixItem
Revenue and attendance correlation per instructor.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| instructor_name | string | Yes | Instructor full name |
| total_revenue | float | Yes | Total revenue generated |
| avg_attendance_pct | float | Yes | Average attendance percentage across their groups |

**Example:**
```json
{
  "instructor_name": "Ahmed Hassan",
  "total_revenue": 75000.0,
  "avg_attendance_pct": 92.5
}
```

---

### ScheduleUtilizationItem
Schedule slot utilization statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| day | string | Yes | Day of week |
| time_start | string | Yes | Start time (HH:MM) |
| total_enrolled | integer | Yes | Total students enrolled in slots at this time |
| total_capacity | integer | Yes | Total capacity of all groups at this time |
| utilization_pct | float | Yes | Percentage utilized |

**Example:**
```json
{
  "day": "Saturday",
  "time_start": "14:00",
  "total_enrolled": 45,
  "total_capacity": 60,
  "utilization_pct": 75.0
}
```

---

### FlightRiskStudentItem
Student flagged as likely to drop out.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_name | string | Yes | Student full name |
| course_name | string | Yes | Course name |
| amount_owed | float | Yes | Outstanding balance (negative) |
| sessions_missed | integer | Yes | Recent missed sessions count |

**Example:**
```json
{
  "student_name": "Omar Mohamed",
  "course_name": "Robotics Fundamentals",
  "amount_owed": -500.0,
  "sessions_missed": 3
}
```

---

### UserEngagementItem
Daily user engagement metrics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| date | date | Yes | Date (YYYY-MM-DD) |
| daily_active_users | integer | Yes | Unique active users |
| total_sessions | integer | Yes | Total user sessions |
| avg_session_duration_minutes | float | Yes | Average session duration |
| feature_usage | dict[string, int] | Yes | Feature usage counts |

**Example:**
```json
{
  "date": "2026-04-05",
  "daily_active_users": 25,
  "total_sessions": 85,
  "avg_session_duration_minutes": 45.5,
  "feature_usage": {
    "attendance_marking": 45,
    "student_search": 30,
    "receipt_creation": 10
  }
}
```

---

### RetentionCohortItem
Cohort-based retention analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cohort_month | string | Yes | Month of initial enrollment (YYYY-MM) |
| initial_enrollments | integer | Yes | Students who started in this cohort |
| retention_by_month | dict[string, int] | Yes | Absolute counts per month |
| retention_rates | dict[string, float] | Yes | Retention percentages per month |

**Example:**
```json
{
  "cohort_month": "2026-01",
  "initial_enrollments": 50,
  "retention_by_month": {
    "month_1": 48,
    "month_2": 45,
    "month_3": 42
  },
  "retention_rates": {
    "month_1": 96.0,
    "month_2": 90.0,
    "month_3": 84.0
  }
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
      "loc": ["query", "days"],
      "msg": "ensure this value is less than or equal to 90",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Cohort Analysis Explanation

The retention analysis endpoint uses **cohort analysis** methodology:

1. **Cohort Definition**: Students who enrolled in the same month form a cohort
2. **Tracking**: System tracks how many from each cohort remain active over subsequent months
3. **Calculation**: 
   - `retention_by_month` = absolute student counts still active
   - `retention_rates` = percentage of initial cohort still active

**Example**: A cohort starting with 50 students in January:
- Month 1: 48 students (96% retention)
- Month 2: 45 students (90% retention)
- Month 3: 42 students (84% retention)

This helps identify when students typically drop out and evaluate retention strategies.

---

[← Back to Analytics API Overview](../analytics.md)
