# Business Intelligence (BI) Analytics API

Advanced analytics for trends, retention, instructor performance, and student risk factor analysis.

---

## Endpoints

### 1. Get Enrollment Trend
`GET /analytics/bi/enrollment-trend`

Returns daily new enrollment counts over time to visualize growth trends.

**Query Parameters:**
- `cutoff` (optional): The start date for the analysis (YYYY-MM-DD). Defaults to 90 days ago.

**Response Body:** `ApiResponse[list[EnrollmentTrendItem]]`
```json
[
  {
    "day": "2026-04-15",
    "new_enrollments": 12
  }
]
```

---

### 2. Get Retention Metrics
`GET /analytics/bi/retention`

Returns current enrollment retention and dropout counts grouped by course.

**Response Body:** `ApiResponse[list[RetentionMetricsResponse]]`
```json
[
  {
    "course_name": "Robotics 101",
    "active_count": 80,
    "dropped_count": 5,
    "total_enrollments": 85
  }
]
```

---

### 3. Get Instructor Performance
`GET /analytics/bi/instructor-performance`

Provides operational volume metrics (groups handled and total students) per instructor.

**Response Body:** `ApiResponse[list[InstructorPerformanceItem]]`
```json
[
  {
    "instructor_name": "John Doe",
    "active_groups": 4,
    "active_students": 45
  }
]
```

---

### 4. Get Level Retention Funnel
`GET /analytics/bi/retention-funnel`

Shows a progression funnel of how many students reach which level in a specific course.

**Response Body:** `ApiResponse[list[LevelRetentionFunnelItem]]`
```json
[
  {
    "course_name": "Robotics 101",
    "level_number": 1,
    "student_count": 100
  },
  {
    "course_name": "Robotics 101",
    "level_number": 2,
    "student_count": 65
  }
]
```

---

### 5. Get Instructor Value Matrix
`GET /analytics/bi/instructor-value`

Correlates instructor teaching quality (via attendance percentages) with revenue generated.

**Response Body:** `ApiResponse[list[InstructorValueMatrixItem]]`
```json
[
  {
    "instructor_name": "John Doe",
    "total_revenue": 15000.0,
    "avg_attendance_pct": 92.5
  }
]
```

---

### 6. Get Schedule Utilization
`GET /analytics/bi/schedule-utilization`

Analyzes how well scheduled time slots are being utilized relative to their maximum capacity.

**Response Body:** `ApiResponse[list[ScheduleUtilizationItem]]`
```json
[
  {
    "day": "Monday",
    "time_start": "16:00:00",
    "total_enrolled": 18,
    "total_capacity": 20,
    "utilization_pct": 90.0
  }
]
```

---

### 7. Get Flight-Risk Students
`GET /analytics/bi/flight-risk`

Uses a heuristic model based on missed sessions and outstanding debt to identify students likely to drop out.

**Response Body:** `ApiResponse[list[FlightRiskStudentItem]]`
```json
[
  {
    "student_name": "Alice Wonderland",
    "course_name": "Advanced AI",
    "amount_owed": 1200.0,
    "sessions_missed": 3
  }
]
```

---

### 8. Get Retention Cohort Analysis
`GET /analytics/bi/retention-analysis`

Provides a longitudinal look at student retention by grouping enrollments into monthly cohorts.

**Query Parameters:**
- `months` (optional): Number of months to look back (1-12, default: 6).

**Response Body:** `ApiResponse[list[RetentionCohortItem]]`
```json
[
  {
    "cohort_month": "2026-01",
    "initial_enrollments": 50,
    "retention_by_month": {
      "Month 0": "100%",
      "Current": "88.5%"
    },
    "retention_rates": {
        "overall_retention_pct": 88.5
    }
  }
]
```
