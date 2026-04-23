# Group Details API Contract

**Version:** 1.0.0  
**Last Updated:** April 23, 2026  
**Base URL:** `/api/v1`

---

## 1. Overview

The Group Details API provides comprehensive endpoints for managing group levels, viewing attendance grids, tracking payments, and managing student enrollments. It follows the **lookup table pattern** (consistent with Dashboard API) to minimize data duplication and improve performance.

### Key Features
- **DELETE Level:** Soft delete with constraint validation (no sessions/enrollments)
- **Levels Detailed:** All levels with sessions, enrollment counts, and payment summaries
- **Attendance Grid:** Roster + sessions with O(1) attendance lookup
- **Payments:** Per-level payment breakdown with collection rates
- **Enrollments:** Grouped by level with transfer options

### Lookup Table Pattern

Responses use lookup tables to avoid data duplication:

```typescript
// Lookup tables at top level
courses: Record<int, CourseInfo>      // course_id -> course info
instructors: Record<int, InstructorInfo>  // instructor_id -> instructor info
students: Record<int, StudentInfo>    // student_id -> student info

// Main data references IDs only
levels: LevelDTO[]  // Each level has course_id, instructor_id
```

This pattern reduces payload size and ensures data consistency.

---

## 2. Authentication

All endpoints require **JWT Bearer token authentication**.

### Required Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | `Bearer {jwt_token}` | Yes |
| `Content-Type` | `application/json` | Yes |

### Authorization Matrix

| Endpoint | HTTP Method | Required Role |
|----------|-------------|---------------|
| DELETE /levels/{n} | DELETE | `admin` |
| GET /levels/detailed | GET | Any authenticated user |
| GET /attendance | GET | Any authenticated user |
| GET /finance/payments | GET | Any authenticated user |
| GET /enrollments/all | GET | Any authenticated user |

---

## 3. Endpoint: DELETE /academics/groups/{group_id}/levels/{level_number}

Soft delete a level if it has no sessions or active enrollments.

### 3.1 Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `int` | Yes | Group ID (positive integer) |
| `level_number` | `int` | Yes | Level number to delete (1, 2, 3, ...) |

#### Example Request

```http
DELETE /api/v1/academics/groups/101/levels/3
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3.2 Response

#### Success (200 OK)

```json
{
  "success": true,
  "data": {
    "level_id": 45,
    "level_number": 3,
    "group_id": 101,
    "deleted_at": "2026-04-23T10:30:00.000Z"
  },
  "message": "Level 3 deleted successfully."
}
```

#### Error Responses

**404 Not Found - Level doesn't exist**
```json
{
  "success": false,
  "error": "Level 3 not found for group 101"
}
```

**409 Conflict - Has sessions**
```json
{
  "success": false,
  "error": "Cannot delete level 3: it has scheduled sessions"
}
```

**409 Conflict - Has enrollments**
```json
{
  "success": false,
  "error": "Cannot delete level 3: it has active enrollments"
}
```

---

## 4. Endpoint: GET /academics/groups/{group_id}/levels/detailed

Get all levels with sessions, enrollment counts, and payment summaries.

### 4.1 Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `int` | Yes | Group ID |

#### Example Request

```http
GET /api/v1/academics/groups/101/levels/detailed
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4.2 Response Schema

#### GroupLevelsDetailedResponseDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | No | Group ID |
| `generated_at` | `string` (ISO 8601) | No | Server timestamp |
| `cache_ttl` | `int` | No | Cache TTL in seconds (300) |
| `courses` | `Record<int, CourseLookupDTO>` | No | Lookup table: course_id -> course info |
| `instructors` | `Record<int, InstructorLookupDTO>` | No | Lookup table: instructor_id -> instructor info |
| `levels` | `LevelWithSessionsDTO[]` | No | All levels for the group |

#### CourseLookupDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `course_id` | `int` | No | Course ID |
| `course_name` | `string` | No | Course name |

#### InstructorLookupDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `instructor_id` | `int` | No | Instructor ID |
| `instructor_name` | `string` | No | Full name |

#### LevelWithSessionsDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `level_number` | `int` | No | Level number |
| `level_id` | `int` | No | Level record ID |
| `course_id` | `int` | No | References courses lookup |
| `instructor_id` | `int` | No | References instructors lookup |
| `status` | `string` | No | `active`, `completed`, `cancelled` |
| `start_date` | `string` (YYYY-MM-DD) | Yes | First session date |
| `end_date` | `string` (YYYY-MM-DD) | Yes | Last session date |
| `sessions` | `SessionInLevelDTO[]` | No | All sessions for this level |
| `students_count` | `int` | No | Total enrollments |
| `students_completed` | `int` | No | Completed count |
| `students_dropped` | `int` | No | Dropped count |
| `payment_summary` | `PaymentSummaryDTO` | No | Aggregated payment data |

#### SessionInLevelDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `session_id` | `int` | No | Session ID |
| `session_number` | `int` | No | Sequential number within level |
| `date` | `string` (YYYY-MM-DD) | No | Session date |
| `time_start` | `string` (HH:MM) | No | Start time |
| `time_end` | `string` (HH:MM) | No | End time |
| `status` | `string` | No | `scheduled`, `completed`, `cancelled` |
| `is_extra_session` | `boolean` | No | True if extra/make-up |
| `actual_instructor_id` | `int` | Yes | Substitute instructor (null if same) |
| `is_substitute` | `boolean` | No | True if substitute taught |

#### PaymentSummaryDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `total_expected` | `number` | No | Sum of (amount_due - discount) |
| `total_collected` | `number` | No | Sum of payments minus refunds |
| `total_due` | `number` | No | Outstanding balance |
| `collection_rate` | `number` | No | 0.0 to 1.0 (collected/expected) |
| `unpaid_students_count` | `int` | No | Students with balance > 0 |

### 4.3 Example Response

```json
{
  "success": true,
  "data": {
    "group_id": 101,
    "generated_at": "2026-04-23T10:30:00.000Z",
    "cache_ttl": 300,
    "courses": {
      "1": {
        "course_id": 1,
        "course_name": "Robotics Basics"
      }
    },
    "instructors": {
      "5": {
        "instructor_id": 5,
        "instructor_name": "Ahmed Hassan"
      }
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
    ]
  },
  "message": "Group levels loaded successfully."
}
```

---

## 5. Endpoint: GET /academics/groups/{group_id}/attendance

Get attendance grid for a specific level.

### 5.1 Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `int` | Yes | Group ID |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `level_number` | `int` | Yes | Level number to get attendance for |

#### Example Request

```http
GET /api/v1/academics/groups/101/attendance?level_number=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5.2 Response Schema

#### GroupAttendanceResponseDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | No | Group ID |
| `level_number` | `int` | No | Level number |
| `generated_at` | `string` (ISO 8601) | No | Server timestamp |
| `cache_ttl` | `int` | No | Cache TTL (300) |
| `roster` | `AttendanceRosterStudentDTO[]` | No | Active enrollments |
| `sessions` | `AttendanceSessionDTO[]` | No | Sessions with attendance maps |

#### AttendanceRosterStudentDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `student_id` | `int` | No | Student ID |
| `student_name` | `string` | No | Full name |
| `enrollment_id` | `int` | No | Enrollment record ID |
| `billing_status` | `string` | No | `paid` or `due` |
| `joined_at` | `string` (ISO 8601) | Yes | Enrollment date |

#### AttendanceSessionDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `session_id` | `int` | No | Session ID |
| `session_number` | `int` | No | Sequential number |
| `date` | `string` (YYYY-MM-DD) | No | Session date |
| `time_start` | `string` (HH:MM) | No | Start time |
| `time_end` | `string` (HH:MM) | No | End time |
| `status` | `string` | No | `scheduled`, `completed`, `cancelled` |
| `is_extra_session` | `boolean` | No | True if extra/make-up |
| `attendance` | `Record<int, string>` | No | Map: student_id -> status (see below) |

**Attendance Status Values:**
- `"present"` - Student was present
- `"absent"` - Student was absent
- `"excused"` - Excused absence
- `"late"` - Late arrival
- `null` - Not marked yet

### 5.3 Example Response

```json
{
  "success": true,
  "data": {
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
      },
      {
        "student_id": 2002,
        "student_name": "Laila Ahmad",
        "enrollment_id": 5002,
        "billing_status": "due",
        "joined_at": "2026-01-12T08:00:00.000Z"
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
          "2002": "present"
        }
      },
      {
        "session_id": 1002,
        "session_number": 2,
        "date": "2026-01-22",
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
  },
  "message": "Attendance grid loaded successfully."
}
```

### 5.4 Frontend Integration Notes

**Rendering Attendance Grid:**

```typescript
// Use the attendance map for O(1) lookup
const attendanceStatus = session.attendance[studentId];
// Returns: "present" | "absent" | "excused" | "late" | undefined
```

**Grid Layout:**
- Rows: Students (from roster, sorted by name)
- Columns: Sessions (sorted by session_number)
- Cells: attendance[student_id] for each session

---

## 6. Endpoint: GET /finance/groups/{group_id}/payments

Get payments grouped by level with summary statistics.

### 6.1 Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `int` | Yes | Group ID |

#### Example Request

```http
GET /api/v1/finance/groups/101/payments
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 6.2 Response Schema

#### GroupPaymentsResponseDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | No | Group ID |
| `generated_at` | `string` (ISO 8601) | No | Server timestamp |
| `cache_ttl` | `int` | No | Cache TTL (300) |
| `summary` | `GroupPaymentsSummaryDTO` | No | Overall statistics |
| `by_level` | `LevelPaymentSummaryDTO[]` | No | Per-level breakdown |

#### GroupPaymentsSummaryDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `total_expected_all_levels` | `number` | No | Sum of all expected payments |
| `total_collected_all_levels` | `number` | No | Sum of all collected payments |
| `total_due_all_levels` | `number` | No | Total outstanding balance |
| `collection_rate` | `number` | No | 0.0 to 1.0 (collected/expected) |

#### LevelPaymentSummaryDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `level_number` | `int` | No | Level number |
| `level_status` | `string` | No | `active`, `completed`, `cancelled` |
| `course_name` | `string` | No | Course name |
| `expected` | `number` | No | Expected amount for level |
| `collected` | `number` | No | Collected amount |
| `due` | `number` | No | Outstanding balance |
| `total_students` | `int` | No | Number of students in level |
| `paid_count` | `int` | No | Students fully paid |
| `unpaid_count` | `int` | No | Students with balance > 0 |
| `payments` | `PaymentInLevelDTO[]` | No | Individual payment records |

#### PaymentInLevelDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `payment_id` | `int` | No | Payment ID |
| `student_id` | `int` | No | Student ID |
| `student_name` | `string` | No | Student name |
| `amount` | `number` | No | Payment amount |
| `discount_amount` | `number` | No | Discount applied |
| `payment_date` | `string` (YYYY-MM-DD) | No | Payment date |
| `payment_method` | `string` | No | `cash`, `card`, `bank_transfer`, `wallet` |
| `status` | `string` | No | `completed`, `pending`, `failed`, `refunded` |
| `receipt_number` | `string` | Yes | Receipt number if available |
| `transaction_type` | `string` | No | `payment`, `refund`, `adjustment` |

### 6.3 Example Response

```json
{
  "success": true,
  "data": {
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
  },
  "message": "Group payments loaded successfully."
}
```

---

## 7. Endpoint: GET /academics/groups/{group_id}/enrollments/all

Get all enrollments grouped by level with transfer options.

### 7.1 Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `int` | Yes | Group ID |

#### Example Request

```http
GET /api/v1/academics/groups/101/enrollments/all
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 7.2 Response Schema

#### GroupEnrollmentsResponseDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | No | Group ID |
| `generated_at` | `string` (ISO 8601) | No | Server timestamp |
| `cache_ttl` | `int` | No | Cache TTL (300) |
| `students` | `Record<int, StudentLookupDTO>` | No | Lookup table: student_id -> student info |
| `grouped_by_level` | `LevelWithEnrollmentsDTO[]` | No | Enrollments per level |
| `transfer_options` | `TransferOptionDTO[]` | No | Available groups for transfer |

#### StudentLookupDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `student_id` | `int` | No | Student ID |
| `student_name` | `string` | No | Full name |
| `phone` | `string` | Yes | Phone number |
| `parent_name` | `string` | Yes | Primary parent name |

#### LevelWithEnrollmentsDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `level_number` | `int` | No | Level number |
| `level_status` | `string` | No | `active`, `completed`, `cancelled` |
| `course_name` | `string` | No | Course name |
| `enrollments` | `EnrollmentInLevelDTO[]` | No | Enrollments in this level |
| `summary` | `LevelEnrollmentSummaryDTO` | No | Aggregated stats |

#### EnrollmentInLevelDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `enrollment_id` | `int` | No | Enrollment ID |
| `student_id` | `int` | No | References students lookup |
| `status` | `string` | No | `active`, `completed`, `dropped` |
| `enrolled_at` | `string` (ISO 8601) | No | Enrollment date |
| `dropped_at` | `string` (ISO 8601) | Yes | Drop date if dropped |
| `sessions_attended` | `int` | No | Count of present/late |
| `sessions_total` | `int` | No | Count of all sessions |
| `payment_status` | `string` | No | `paid`, `due`, `partial` |
| `amount_due` | `number` | No | Original amount due |
| `amount_paid` | `number` | No | Total paid |
| `discount_applied` | `number` | No | Discount amount |
| `can_transfer` | `boolean` | No | True if active |
| `can_drop` | `boolean` | No | True if active |

#### LevelEnrollmentSummaryDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `total` | `int` | No | Total enrollments |
| `active` | `int` | No | Active count |
| `completed` | `int` | No | Completed count |
| `dropped` | `int` | No | Dropped count |
| `paid` | `int` | No | Fully paid count |
| `unpaid` | `int` | No | Unpaid count |

#### TransferOptionDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | No | Target group ID |
| `group_name` | `string` | No | Group name |
| `course_name` | `string` | No | Course name |
| `available_slots` | `int` | No | Available capacity |

### 7.3 Example Response

```json
{
  "success": true,
  "data": {
    "group_id": 101,
    "generated_at": "2026-04-23T10:30:00.000Z",
    "cache_ttl": 300,
    "students": {
      "2001": {
        "student_id": 2001,
        "student_name": "Omar Khaled",
        "phone": "+20 100 123 4567",
        "parent_name": "Khaled Ibrahim"
      },
      "2002": {
        "student_id": 2002,
        "student_name": "Laila Ahmad",
        "phone": "+20 101 987 6543",
        "parent_name": "Ahmad Hassan"
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
            "status": "completed",
            "enrolled_at": "2026-01-10T08:00:00.000Z",
            "dropped_at": null,
            "sessions_attended": 12,
            "sessions_total": 12,
            "payment_status": "paid",
            "amount_due": 3000.00,
            "amount_paid": 3000.00,
            "discount_applied": 0.00,
            "can_transfer": false,
            "can_drop": false
          }
        ],
        "summary": {
          "total": 12,
          "active": 0,
          "completed": 10,
          "dropped": 2,
          "paid": 11,
          "unpaid": 1
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
  },
  "message": "Group enrollments loaded successfully."
}
```

---

## 8. Common Patterns

### 8.1 Cache Handling

All responses include `cache_ttl` (300 seconds) and `generated_at`:

```typescript
const CACHE_TTL = response.data.cache_ttl * 1000; // Convert to ms
const isStale = Date.now() - new Date(response.data.generated_at).getTime() > CACHE_TTL;
```

### 8.2 Lookup Table Usage

Access lookup tables by ID:

```typescript
const courseName = response.data.courses[level.course_id]?.course_name;
const instructorName = response.data.instructors[level.instructor_id]?.instructor_name;
const studentName = response.data.students[enrollment.student_id]?.student_name;
```

### 8.3 Error Handling

Standard error response structure:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "optional_error_code"
}
```

Common HTTP status codes:
- `200` - Success
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `409` - Conflict (business rule violation)
- `422` - Validation error

---

## 9. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | April 23, 2026 | Initial release with 5 endpoints |

---

## 10. Support

For API integration questions or issues:
- Review the Dashboard API documentation for lookup table patterns
- Check the codebase for DTO definitions in `app/modules/academics/schemas/group_details_schemas.py`
- Contact the backend team for schema clarifications
