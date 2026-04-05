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

### BI (Business Intelligence)

#### 5. Get enrollment trend over time
**GET** `/api/v1/analytics/bi/enrollment-trend`

**Query Parameters:**
- `cutoff` - string (optional)

**Response (200):** `ApiResponse<list<EnrollmentTrendDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 6. Get retention metrics by course
**GET** `/api/v1/analytics/bi/retention`

**Response (200):** `ApiResponse<list<RetentionMetricsDTO>>`

---

#### 7. Get instructor performance metrics
**GET** `/api/v1/analytics/bi/instructor-performance`

**Response (200):** `ApiResponse<list<InstructorPerformanceDTO>>`

---

#### 8. Get level retention funnel
**GET** `/api/v1/analytics/bi/retention-funnel`

**Response (200):** `ApiResponse<list<LevelRetentionFunnelDTO>>`

---

#### 9. Get instructor value matrix
**GET** `/api/v1/analytics/bi/instructor-value`

**Response (200):** `ApiResponse<list<InstructorValueMatrixDTO>>`

---

#### 10. Get schedule utilization
**GET** `/api/v1/analytics/bi/schedule-utilization`

**Response (200):** `ApiResponse<list<ScheduleUtilizationDTO>>`

---

#### 11. Get flight-risk students
**GET** `/api/v1/analytics/bi/flight-risk`

**Response (200):** `ApiResponse<list<FlightRiskStudentDTO>>`

---

### Competition Analytics

#### 12. Get competition fee summary
**GET** `/api/v1/analytics/competitions/fee-summary`

**Response (200):** `ApiResponse<list<CompetitionFeeSummaryDTO>>`

---

### Financial Analytics

#### 13. Get revenue breakdown by date
**GET** `/api/v1/analytics/finance/revenue-by-date`

**Query Parameters:**
- `start` - string (required) - Format: YYYY-MM-DD
- `end` - string (required) - Format: YYYY-MM-DD

**Response (200):** `ApiResponse<list<RevenueByDateDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 14. Get revenue breakdown by payment method
**GET** `/api/v1/analytics/finance/revenue-by-method`

**Query Parameters:**
- `start` - string (required) - Format: YYYY-MM-DD
- `end` - string (required) - Format: YYYY-MM-DD

**Response (200):** `ApiResponse<list<RevenueByMethodDTO>>`

**Error Response (422):** `HTTPValidationError`

---

#### 15. Get outstanding balances by group
**GET** `/api/v1/analytics/finance/outstanding-by-group`

**Response (200):** `ApiResponse<list<OutstandingByGroupDTO>>`

---

#### 16. Get top debtors
**GET** `/api/v1/analytics/finance/top-debtors`

**Query Parameters:**
- `limit` - integer (optional)

**Response (200):** `ApiResponse<list<TopDebtorDTO>>`

**Error Response (422):** `HTTPValidationError`
