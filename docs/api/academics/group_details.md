# Academics API - Group Details Router

Router source: `app/api/routers/academics/group_details_router.py`

Mounted prefix: `/api/v1`

---

## Overview

The Group Details Router provides comprehensive endpoints for managing and viewing group-level details including:
- Level management with sessions and payment summaries
- Attendance grids with roster and session data
- Payment tracking grouped by level
- Enrollment management with transfer options

**Key Features:**
- Lookup table pattern to minimize data duplication
- Optional query parameters for filtering (e.g., `?level_number=3`)
- Cache-friendly responses with `cache_ttl` hints
- Consistent `ApiResponse[T]` envelope format

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_any`: GET endpoints (any authenticated user)
- `require_admin`: DELETE endpoint (admin only)

Common auth errors:
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions (e.g., non-admin attempting DELETE)

---

## DTOs and Schemas

### Lookup Tables

Responses use lookup tables to avoid data duplication. Access data like this:

```typescript
const courseName = response.data.courses[level.course_id]?.course_name;
const studentName = response.data.students[enrollment.student_id]?.student_name;
```

#### CourseLookupDTO
```json
{
  "course_id": 1,
  "course_name": "Robotics Basics"
}
```

#### InstructorLookupDTO
```json
{
  "instructor_id": 5,
  "instructor_name": "Ahmed Hassan"
}
```

#### StudentLookupDTO
```json
{
  "student_id": 2001,
  "student_name": "Omar Khaled",
  "phone": "+20 100 123 4567",
  "parent_name": "Khaled Ibrahim"
}
```

### Level Detail DTOs

#### SessionInLevelDTO
```json
{
  "session_id": 1001,
  "session_number": 1,
  "date": "2026-01-15",
  "time_start": "15:00",
  "time_end": "16:30",
  "status": "completed",
  "is_extra_session": false,
  "actual_instructor_id": 5,
  "is_substitute": false
}
```

#### PaymentSummaryDTO
```json
{
  "total_expected": 36000.00,
  "total_collected": 35000.00,
  "total_due": 1000.00,
  "collection_rate": 0.972,
  "unpaid_students_count": 1
}
```

#### LevelWithSessionsDTO
```json
{
  "level_number": 1,
  "level_id": 10,
  "course_id": 1,
  "instructor_id": 5,
  "status": "completed",
  "start_date": "2026-01-15",
  "end_date": "2026-03-15",
  "sessions": [
    {
      "session_id": 1001,
      "session_number": 1,
      "date": "2026-01-15",
      "time_start": "15:00",
      "time_end": "16:30",
      "status": "completed",
      "is_extra_session": false,
      "actual_instructor_id": 5,
      "is_substitute": false
    }
  ],
  "students_count": 12,
  "students_completed": 10,
  "students_dropped": 2,
  "payment_summary": {
    "total_expected": 36000.00,
    "total_collected": 35000.00,
    "total_due": 1000.00,
    "collection_rate": 0.972,
    "unpaid_students_count": 1
  }
}
```

### Attendance DTOs

#### AttendanceRosterStudentDTO
```json
{
  "student_id": 2001,
  "student_name": "Omar Khaled",
  "enrollment_id": 5001,
  "billing_status": "paid",
  "joined_at": "2026-01-10T08:00:00.000Z"
}
```

#### AttendanceSessionDTO
```json
{
  "session_id": 1001,
  "session_number": 1,
  "date": "2026-01-15",
  "time_start": "15:00",
  "time_end": "16:30",
  "status": "completed",
  "is_extra_session": false,
  "attendance": {
    "2001": "present",
    "2002": "absent"
  }
}
```

**Attendance status values:**
- `"present"` - Student was present
- `"absent"` - Student was absent
- `"excused"` - Excused absence
- `"late"` - Late arrival
- `null` - Not marked yet

### Payment DTOs

#### PaymentInLevelDTO
```json
{
  "payment_id": 8001,
  "student_id": 2001,
  "student_name": "Omar Khaled",
  "amount": 3000.00,
  "discount_amount": 0.00,
  "payment_date": "2026-01-15",
  "payment_method": "cash",
  "status": "completed",
  "receipt_number": "R-2026-001",
  "transaction_type": "payment"
}
```

#### LevelPaymentSummaryDTO
```json
{
  "level_number": 1,
  "level_status": "completed",
  "course_name": "Robotics Basics",
  "expected": 36000.00,
  "collected": 35000.00,
  "due": 1000.00,
  "total_students": 12,
  "paid_count": 11,
  "unpaid_count": 1,
  "payments": []
}
```

### Enrollment DTOs

#### EnrollmentInLevelDTO
```json
{
  "enrollment_id": 5001,
  "student_id": 2001,
  "status": "active",
  "enrolled_at": "2026-01-10T08:00:00.000Z",
  "dropped_at": null,
  "sessions_attended": 12,
  "sessions_total": 12,
  "payment_status": "paid",
  "amount_due": 3000.00,
  "amount_paid": 3000.00,
  "discount_applied": 0.00,
  "can_transfer": true,
  "can_drop": true
}
```

#### TransferOptionDTO
```json
{
  "group_id": 102,
  "group_name": "Advanced Builders",
  "course_name": "Advanced Robotics",
  "available_slots": 5
}
```

---

## Endpoints

### 1) Delete a Level (Soft Delete)

**DELETE** `/api/v1/academics/groups/{group_id}/levels/{level_number}`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `level_number` (integer, required)

Response:
- `200 OK` -> `ApiResponse<LevelDeleteResultDTO>`:
```json
{
  "level_id": 45,
  "level_number": 3,
  "group_id": 101,
  "deleted_at": "2026-04-23T10:30:00.000Z"
}
```

Errors:
- `401`, `403`
- `404` - Level not found
- `409` - Level has scheduled sessions (cannot delete)
- `409` - Level has active enrollments (cannot delete)

Notes:
- Soft delete: sets `status='deleted'` and `effective_to` timestamp
- Only allowed if level has no sessions and no active enrollments

---

### 2) Get Levels Detailed

**GET** `/api/v1/academics/groups/{group_id}/levels/detailed`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query params:
- `level_number` (optional): Return only this specific level

Response:
- `200 OK` -> `ApiResponse<GroupLevelsDetailedResponseDTO>`:
```json
{
  "group_id": 101,
  "generated_at": "2026-04-23T10:30:00.000Z",
  "cache_ttl": 300,
  "courses": {
    "1": { "course_id": 1, "course_name": "Robotics Basics" }
  },
  "instructors": {
    "5": { "instructor_id": 5, "instructor_name": "Ahmed Hassan" }
  },
  "levels": [
    {
      "level_number": 1,
      "level_id": 10,
      "course_id": 1,
      "instructor_id": 5,
      "status": "completed",
      "start_date": "2026-01-15",
      "end_date": "2026-03-15",
      "sessions": [...],
      "students_count": 12,
      "students_completed": 10,
      "students_dropped": 2,
      "payment_summary": {
        "total_expected": 36000.00,
        "total_collected": 35000.00,
        "total_due": 1000.00,
        "collection_rate": 0.972,
        "unpaid_students_count": 1
      }
    }
  ]
}
```

**With `?level_number=3` query param:** Returns single level in `levels` array.

Errors:
- `401`, `403`, `404`

Notes:
- Returns all levels if `level_number` omitted
- Returns single level if `level_number` provided
- Uses lookup table pattern for courses and instructors
- Response cacheable for 300 seconds

---

### 3) Get Attendance Grid

**GET** `/api/v1/academics/groups/{group_id}/attendance`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query params:
- `level_number` (integer, required): Level to get attendance for

Response:
- `200 OK` -> `ApiResponse<GroupAttendanceResponseDTO>`:
```json
{
  "group_id": 101,
  "level_number": 1,
  "generated_at": "2026-04-23T10:30:00.000Z",
  "cache_ttl": 300,
  "roster": [
    {
      "student_id": 2001,
      "student_name": "Omar Khaled",
      "enrollment_id": 5001,
      "billing_status": "paid",
      "joined_at": "2026-01-10T08:00:00.000Z"
    }
  ],
  "sessions": [
    {
      "session_id": 1001,
      "session_number": 1,
      "date": "2026-01-15",
      "time_start": "15:00",
      "time_end": "16:30",
      "status": "completed",
      "is_extra_session": false,
      "attendance": {
        "2001": "present",
        "2002": "absent"
      }
    }
  ]
}
```

**Rendering Pattern:**
```typescript
// O(1) lookup for attendance grid
const status = session.attendance[studentId];
// Returns: "present" | "absent" | "excused" | "late" | undefined
```

Errors:
- `401`, `403`, `404`
- `422` - Missing required `level_number` query param

Notes:
- Roster provides student list with billing status
- Sessions include attendance map keyed by student_id
- Grid layout: rows=roster (students), columns=sessions

---

### 4) Get Group Payments

**GET** `/api/v1/finance/groups/{group_id}/payments`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupPaymentsResponseDTO>`:
```json
{
  "group_id": 101,
  "generated_at": "2026-04-23T10:30:00.000Z",
  "cache_ttl": 300,
  "summary": {
    "total_expected_all_levels": 72000.00,
    "total_collected_all_levels": 65000.00,
    "total_due_all_levels": 7000.00,
    "collection_rate": 0.903
  },
  "by_level": [
    {
      "level_number": 1,
      "level_status": "completed",
      "course_name": "Robotics Basics",
      "expected": 36000.00,
      "collected": 35000.00,
      "due": 1000.00,
      "total_students": 12,
      "paid_count": 11,
      "unpaid_count": 1,
      "payments": [
        {
          "payment_id": 8001,
          "student_id": 2001,
          "student_name": "Omar Khaled",
          "amount": 3000.00,
          "discount_amount": 0.00,
          "payment_date": "2026-01-15",
          "payment_method": "cash",
          "status": "completed",
          "receipt_number": "R-2026-001",
          "transaction_type": "payment"
        }
      ]
    }
  ]
}
```

Errors:
- `401`, `403`, `404`

Notes:
- Payments grouped by level for easy per-level analysis
- Transaction types: `payment`, `refund`, `adjustment`
- Payment methods: `cash`, `card`, `bank_transfer`, `wallet`

---

### 5) Get Group Enrollments

**GET** `/api/v1/academics/groups/{group_id}/enrollments/all`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupEnrollmentsResponseDTO>`:
```json
{
  "group_id": 101,
  "generated_at": "2026-04-23T10:30:00.000Z",
  "cache_ttl": 300,
  "students": {
    "2001": {
      "student_id": 2001,
      "student_name": "Omar Khaled",
      "phone": "+20 100 123 4567",
      "parent_name": "Khaled Ibrahim"
    }
  },
  "grouped_by_level": [
    {
      "level_number": 1,
      "level_status": "completed",
      "course_name": "Robotics Basics",
      "enrollments": [
        {
          "enrollment_id": 5001,
          "student_id": 2001,
          "status": "active",
          "enrolled_at": "2026-01-10T08:00:00.000Z",
          "dropped_at": null,
          "sessions_attended": 12,
          "sessions_total": 12,
          "payment_status": "paid",
          "amount_due": 3000.00,
          "amount_paid": 3000.00,
          "discount_applied": 0.00,
          "can_transfer": true,
          "can_drop": true
        }
      ],
      "summary": {
        "total": 12,
        "active": 8,
        "completed": 10,
        "dropped": 2,
        "paid": 10,
        "unpaid": 2
      }
    }
  ],
  "transfer_options": [
    {
      "group_id": 102,
      "group_name": "Advanced Builders",
      "course_name": "Advanced Robotics",
      "available_slots": 5
    }
  ]
}
```

Errors:
- `401`, `403`, `404`

Notes:
- Students lookup table for name/phone/parent info
- Enrollments grouped by level
- `can_transfer` and `can_drop` flags for UI action buttons
- Transfer options show active groups with available capacity

---

## Router Notes

- The Group Details router exposes **5 endpoints** for comprehensive group management.
- All GET responses include `cache_ttl: 300` (5 minutes) for frontend caching.
- Lookup tables (courses, instructors, students) eliminate data duplication.
- Query parameters enable flexible data retrieval (e.g., specific level vs all levels).
- DELETE endpoint enforces business rules (no sessions/enrollments constraint).
