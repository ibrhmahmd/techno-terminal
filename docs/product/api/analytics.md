# Analytics API Reference

Base paths: `/api/v1/analytics`

---

## 🔐 Authentication
All requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### DashboardSummaryPublic
```json
{
  "active_enrollments": 150,
  "today_sessions_count": 8
}
```

### SessionSummaryPublic
```json
{
  "session_id": 1,
  "group_id": 1,
  "session_date": "2026-04-03",
  "start_time": "14:00:00",
  "end_time": "16:00:00",
  "instructor_name": "Ahmed Hassan"
}
```

### UnpaidAttendeeDTO
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "parent_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "total_balance": -500.0
}
```

### GroupRosterRowDTO
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

### AttendanceHeatmapRowDTO
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

### EnrollmentTrendDTO (BI)
```json
{
  "day": "2026-04-01",
  "new_enrollments": 5
}
```

### RetentionMetricsDTO (BI)
```json
{
  "course_name": "Robotics Fundamentals",
  "active_count": 45,
  "dropped_count": 5,
  "total_enrollments": 50
}
```

### InstructorPerformanceDTO (BI)
```json
{
  "instructor_name": "Ahmed Hassan",
  "active_groups": 4,
  "active_students": 32
}
```

### LevelRetentionFunnelDTO (BI)
```json
{
  "course_name": "Robotics Fundamentals",
  "level_number": 1,
  "student_count": 50
}
```

### InstructorValueMatrixDTO (BI)
```json
{
  "instructor_name": "Ahmed Hassan",
  "total_revenue": 75000.0,
  "avg_attendance_pct": 92.5
}
```

### ScheduleUtilizationDTO (BI)
```json
{
  "day": "Saturday",
  "time_start": "14:00",
  "total_enrolled": 45,
  "total_capacity": 60,
  "utilization_pct": 75.0
}
```

### FlightRiskStudentDTO (BI)
```json
{
  "student_name": "Omar Mohamed",
  "course_name": "Robotics Fundamentals",
  "amount_owed": -500.0,
  "sessions_missed": 3
}
```

### CompetitionFeeSummaryDTO
```json
{
  "competition_id": 1,
  "competition_name": "National Robotics Championship",
  "competition_date": "2026-05-15",
  "team_count": 8,
  "member_count": 24,
  "fees_collected": 12000.0,
  "fees_outstanding": 3000.0
}
```

### RevenueByDateDTO
```json
{
  "day": "2026-04-01",
  "net_revenue": 15000.0
}
```

### RevenueByMethodDTO
```json
{
  "payment_method": "cash",
  "net_revenue": 8000.0,
  "receipt_count": 12
}
```

### OutstandingByGroupDTO
```json
{
  "group_id": 1,
  "group_name": "Sat 2PM Robotics",
  "course_name": "Robotics Fundamentals",
  "students_with_balance": 5,
  "total_outstanding": 2500.0
}
```

### TopDebtorDTO
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "parent_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "total_outstanding": -500.0
}
```

### RevenueMetricsDTO
```json
{
  "period_start": "2026-01-01",
  "period_end": "2026-06-30",
  "total_revenue": 450000.0,
  "total_receipts": 320,
  "avg_revenue_per_receipt": 1406.25,
  "previous_period_revenue": 420000.0,
  "revenue_change_pct": 7.14,
  "trend_direction": "up",
  "monthly_breakdown": [
    {"day": "2026-01-01", "net_revenue": 75000.0},
    {"day": "2026-02-01", "net_revenue": 72000.0}
  ]
}
```

### StudentProgressDTO
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

### CourseCompletionDTO
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

### RevenueForecastDTO
```json
{
  "month": "2026-07",
  "predicted_revenue": 480000.0,
  "confidence_lower": 384000.0,
  "confidence_upper": 576000.0
}
```

### UserEngagementDTO
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

### RetentionCohortDTO
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

### Dashboard

#### 1. Get high-level dashboard aggregates
**GET** `/api/v1/analytics/dashboard/summary`

**Response (200):** `ApiResponse<DashboardSummaryPublic>`

---

### Academic Analytics

#### 2. Get unpaid attendees for today
**GET** `/api/v1/analytics/academics/unpaid-attendees`

**Query Parameters:**
- `target_date` - string (optional) - Format: YYYY-MM-DD

**Response (200):** `ApiResponse<list<UnpaidAttendeeDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 3. Get group roster
**GET** `/api/v1/analytics/academics/groups/{group_id}/roster`

**Path Parameters:**
- `group_id` - integer (required)

**Query Parameters:**
- `level_number` - integer (required)

**Response (200):** `ApiResponse<list<GroupRosterRowDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 4. Get attendance heatmap for group
**GET** `/api/v1/analytics/academics/groups/{group_id}/heatmap`

**Path Parameters:**
- `group_id` - integer (required)

**Query Parameters:**
- `level_number` - integer (required)

**Response (200):** `ApiResponse<list<AttendanceHeatmapRowDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 5. Get student progress analytics
**GET** `/api/v1/analytics/academics/student-progress`

**Query Parameters:**
- `student_id` - integer (optional) - Filter by specific student ID
- `group_id` - integer (optional) - Filter by specific group ID

**Response (200):** `ApiResponse<list<StudentProgressDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 6. Get course completion rates
**GET** `/api/v1/analytics/academics/course-completion`

**Response (200):** `ApiResponse<list<CourseCompletionDTO>>`

---

### BI (Business Intelligence)

#### 7. Get enrollment trend over time
**GET** `/api/v1/analytics/bi/enrollment-trend`

**Query Parameters:**
- `cutoff` - string (optional)

**Response (200):** `ApiResponse<list<EnrollmentTrendDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 8. Get retention metrics by course
**GET** `/api/v1/analytics/bi/retention`

**Response (200):** `ApiResponse<list<RetentionMetricsDTO>>`

---

#### 9. Get instructor performance metrics
**GET** `/api/v1/analytics/bi/instructor-performance`

**Response (200):** `ApiResponse<list<InstructorPerformanceDTO>>`

---

#### 10. Get level retention funnel
**GET** `/api/v1/analytics/bi/retention-funnel`

**Response (200):** `ApiResponse<list<LevelRetentionFunnelDTO>>`

---

#### 11. Get instructor value matrix
**GET** `/api/v1/analytics/bi/instructor-value`

**Response (200):** `ApiResponse<list<InstructorValueMatrixDTO>>`

---

#### 12. Get schedule utilization
**GET** `/api/v1/analytics/bi/schedule-utilization`

**Response (200):** `ApiResponse<list<ScheduleUtilizationDTO>>`

---

#### 13. Get flight-risk students
**GET** `/api/v1/analytics/bi/flight-risk`

**Response (200):** `ApiResponse<list<FlightRiskStudentDTO>>`

---

#### 14. Get user engagement metrics
**GET** `/api/v1/analytics/bi/user-engagement`

**Query Parameters:**
- `days` - integer (optional, default: 30, min: 1, max: 90) - Number of days to analyze

**Response (200):** `ApiResponse<list<UserEngagementDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 15. Get cohort-based retention analysis
**GET** `/api/v1/analytics/bi/retention-analysis`

**Query Parameters:**
- `months` - integer (optional, default: 6, min: 1, max: 12) - Number of months for cohort analysis

**Response (200):** `ApiResponse<list<RetentionCohortDTO>>`

**Error Response (422):** `HTTPValidationError`

---

### Competition Analytics

#### 16. Get competition fee summary
**GET** `/api/v1/analytics/competitions/fee-summary`

**Response (200):** `ApiResponse<list<CompetitionFeeSummaryDTO>>`

---

### Financial Analytics

#### 17. Get revenue breakdown by date
**GET** `/api/v1/analytics/finance/revenue-by-date`

**Query Parameters:**
- `start` - string (required) - Format: YYYY-MM-DD
- `end` - string (required) - Format: YYYY-MM-DD

**Response (200):** `ApiResponse<list<RevenueByDateDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 18. Get revenue breakdown by payment method
**GET** `/api/v1/analytics/finance/revenue-by-method`

**Query Parameters:**
- `start` - string (required) - Format: YYYY-MM-DD
- `end` - string (required) - Format: YYYY-MM-DD

**Response (200):** `ApiResponse<list<RevenueByMethodDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 19. Get outstanding balances by group
**GET** `/api/v1/analytics/finance/outstanding-by-group`

**Response (200):** `ApiResponse<list<OutstandingByGroupDTO>>`

---

#### 20. Get top debtors
**GET** `/api/v1/analytics/finance/top-debtors`

**Query Parameters:**
- `limit` - integer (optional)

**Response (200):** `ApiResponse<list<TopDebtorDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 21. Get extended revenue metrics
**GET** `/api/v1/analytics/finance/revenue-metrics`

**Query Parameters:**
- `months` - integer (optional, default: 6, min: 1, max: 24) - Number of months to analyze

**Response (200):** `ApiResponse<RevenueMetricsDTO>`

**Error Response (422):** `HTTPValidationError`

---

#### 22. Get revenue forecast
**GET** `/api/v1/analytics/finance/revenue-forecast`

**Query Parameters:**
- `months_ahead` - integer (optional, default: 3, min: 1, max: 12) - Number of months to forecast

**Response (200):** `ApiResponse<list<RevenueForecastDTO>>`

**Error Response (422):** `HTTPValidationError`
