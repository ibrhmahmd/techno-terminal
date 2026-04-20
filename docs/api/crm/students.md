# CRM Students API

Student management endpoints for the CRM module.

**Base Path:** `/crm`  
**Authentication:** JWT Bearer token required for all endpoints.

---

## List & Search Endpoints

### GET /crm/students

List and search students with pagination.

**Authentication:** `require_any` (any authenticated user)

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| q | string | No | - | min 1, max 100 chars | Search by name or phone |
| skip | integer | No | 0 | ≥ 0 | Pagination offset |
| limit | integer | No | 50 | 1-200 | Page size |

**Response:** `PaginatedResponse<StudentListItem>`

```json
{
  "data": [
    {
      "id": 1,
      "full_name": "John Doe",
      "phone": "+1234567890",
      "status": "active",
      "date_of_birth": "2010-01-15",
      "gender": "male"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

**Error Codes:**
- 401: Unauthorized

---

### GET /crm/students/grouped

Group students by status, gender, or age bucket.

**Authentication:** `require_admin`

**Query Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| group_by | string | No | status | Group by: status, gender, age_bucket |
| include_inactive | boolean | No | false | Include inactive students |

**Response:** `ApiResponse<StudentGroupedResultDTO>`

---

### GET /crm/students/waiting-list

Get students on the waiting list, ordered by priority.

**Authentication:** `require_admin`

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| skip | integer | No | 0 | ≥ 0 | Pagination offset |
| limit | integer | No | 200 | 1-200 | Page size |
| order_by_priority | boolean | No | true | - | Sort by priority |

**Response:** `ApiResponse<List<StudentResponseDTO>>`

---

### GET /crm/students/by-status/{status}

Get students filtered by enrollment status.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| status | string | Yes | active, waiting, inactive, graduated |

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| skip | integer | No | 0 | ≥ 0 | Pagination offset |
| limit | integer | No | 200 | 1-200 | Page size |

**Response:** `ApiResponse<List<StudentResponseDTO>>`

**Error Codes:**
- 400: Invalid status value

---

### GET /crm/students/status-summary

Get counts of students by enrollment status.

**Authentication:** `require_admin`

**Response:** `ApiResponse<StudentStatusSummaryDTO>`

```json
{
  "data": {
    "active": 120,
    "waiting": 15,
    "inactive": 5,
    "graduated": 30
  }
}
```

---

## CRUD Endpoints

### POST /crm/students

Register a new student.

**Authentication:** `require_admin`

**Request Body:** `RegisterStudentCommandDTO`

```json
{
  "full_name": "Jane Smith",
  "date_of_birth": "2012-03-20",
  "gender": "female",
  "phone": "+1234567890",
  "parent_id": 1,
  "notes": "New enrollment"
}
```

**Response:** `ApiResponse<StudentPublic>` (201 Created)

```json
{
  "data": {
    "id": 101,
    "full_name": "Jane Smith",
    "date_of_birth": "2012-03-20",
    "gender": "female",
    "phone": "+1234567890",
    "status": "active",
    "notes": "New enrollment",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "Student registered successfully."
}
```

**Error Codes:**
- 400: Invalid input data
- 401: Unauthorized

---

### GET /crm/students/{student_id}

Get student by ID.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID (positive) |

**Response:** `ApiResponse<StudentPublic>`

**Error Codes:**
- 404: Student not found

---

### PATCH /crm/students/{student_id}

Update student profile.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Request Body:** `UpdateStudentDTO` (all fields optional)

```json
{
  "full_name": "Jane Doe",
  "phone": "+1987654321",
  "notes": "Updated notes"
}
```

**Response:** `ApiResponse<StudentPublic>`

**Error Codes:**
- 400: Invalid input
- 404: Student not found

---

### DELETE /crm/students/{student_id}

Delete a student by ID.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Response:** `ApiResponse<null>`

```json
{
  "data": null,
  "message": "Student deleted successfully."
}
```

**Error Codes:**
- 404: Student not found

---

## Status Management Endpoints

### PATCH /crm/students/{student_id}/status

Update student enrollment status.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Request Body:** `UpdateStudentStatusDTO`

```json
{
  "status": "waiting",
  "notes": "Moving to waiting list"
}
```

**Response:** `ApiResponse<StudentResponseDTO>`

**Error Codes:**
- 400: Invalid status
- 404: Student not found

---

### POST /crm/students/{student_id}/status/toggle

Toggle student status between active and waiting.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| notes | string | No | Audit notes |

**Response:** `ApiResponse<StudentResponseDTO>`

**Error Codes:**
- 400: Cannot toggle (e.g., graduated/inactive)
- 404: Student not found

---

### PATCH /crm/students/{student_id}/waiting-priority

Set waiting list priority.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Request Body:** `SetWaitingPriorityDTO`

```json
{
  "priority": 1,
  "notes": "High priority request"
}
```

**Response:** `ApiResponse<StudentResponseDTO>`

**Error Codes:**
- 404: Student not found or not on waiting list

---

### GET /crm/students/{student_id}/status-history

Get student status change history.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Response:** `ApiResponse<List<dict>>` (audit log entries)

**Error Codes:**
- 404: Student not found

---

## Detail Endpoints

### GET /crm/students/{student_id}/details

Get complete student profile with enrollments, balance, siblings.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Response:** `ApiResponse<StudentWithDetails>`

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
    }
  }
}
```

**Error Codes:**
- 404: Student not found

---

### GET /crm/students/{student_id}/siblings

Get student's siblings.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Response:** `ApiResponse<List<SiblingInfo>>`

```json
{
  "data": [
    {
      "id": 2,
      "full_name": "Jane Doe",
      "date_of_birth": "2012-03-20",
      "age": 12,
      "gender": "female",
      "parent_name": "Parent Name",
      "enrollment_count": 1
    }
  ]
}
```

---

### GET /crm/students/{student_id}/parents

Get all parents linked to a student.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Response:** `ApiResponse<List<ParentPublic>>`

---

## Schema Definitions

### StudentPublic

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Student ID |
| full_name | string | Yes | Full name |
| date_of_birth | date | No | Date of birth (YYYY-MM-DD) |
| gender | string | No | male, female, other |
| phone | string | No | Contact phone |
| status | string | Yes | active, waiting, inactive, graduated |
| notes | string | No | Additional notes |
| is_active | boolean | Yes | Active flag |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

---

### StudentListItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Student ID |
| full_name | string | Yes | Full name |
| phone | string | No | Contact phone |
| status | string | Yes | Enrollment status |
| date_of_birth | date | No | Date of birth |
| gender | string | No | Gender |

---

### StudentWithDetails

Extends `StudentPublic` with additional fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| age | integer | No | Computed age from date_of_birth |
| school_name | string | No | From profile_metadata |
| waiting_since | datetime | No | When added to waiting list |
| waiting_priority | integer | No | Waiting list priority (1=highest) |
| waiting_notes | string | No | Waiting list notes |
| primary_parent | ParentInfo | No | Primary parent contact |
| current_enrollment | CurrentEnrollmentInfo | No | Active enrollment details |
| enrollments | List<EnrollmentInfo> | Yes | All enrollments |
| balance_summary | StudentBalanceSummary | Yes | Financial summary |
| siblings | List<SiblingInfo> | Yes | Sibling list |
| sessions_attended_count | integer | Yes | Total attended sessions |
| sessions_absent_count | integer | Yes | Total absent sessions |
| last_session_attended | date | No | Last attendance date |
| attendance_stats | AttendanceStatsDTO | Yes | Attendance statistics |

---

### ParentInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Parent ID |
| full_name | string | Yes | Full name |
| phone | string | No | Phone number |
| email | string | No | Email address |
| relationship | string | No | Relationship to student |

---

### CurrentEnrollmentInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| enrollment_id | integer | Yes | Enrollment ID |
| group_id | integer | Yes | Group ID |
| group_name | string | Yes | Group name |
| course_id | integer | Yes | Course ID |
| course_name | string | Yes | Course name |
| level_number | integer | Yes | Level number |
| instructor_name | string | No | Instructor name |

---

### SiblingInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Student ID |
| full_name | string | Yes | Full name |
| date_of_birth | date | No | Date of birth |
| age | integer | No | Computed age |
| gender | string | No | Gender |
| parent_name | string | No | Shared parent's name |
| enrollment_count | integer | Yes | Number of enrollments |

---

### StudentBalanceSummary

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total_due | decimal | Yes | Total amount due |
| total_discount | decimal | Yes | Total discounts applied |
| total_paid | decimal | Yes | Total amount paid |
| net_balance | decimal | Yes | Net balance (due - paid - discount) |

---

### AttendanceStatsDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| attended | integer | Yes | Sessions attended |
| absent | integer | Yes | Sessions absent |
| late | integer | Yes | Sessions late |

---

### RegisterStudentCommandDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| full_name | string | Yes | Full name |
| date_of_birth | date | No | Date of birth (YYYY-MM-DD) |
| gender | string | No | male, female, other |
| phone | string | No | Contact phone |
| parent_id | integer | No | Parent ID (0 or null = none) |
| notes | string | No | Additional notes |

---

### UpdateStudentDTO

All fields optional:

| Field | Type | Description |
|-------|------|-------------|
| full_name | string | Full name |
| date_of_birth | date | Date of birth |
| gender | string | Gender |
| phone | string | Phone number |
| notes | string | Notes |

---

### UpdateStudentStatusDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | string | Yes | active, waiting, inactive, graduated |
| notes | string | No | Audit notes |

---

### SetWaitingPriorityDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| priority | integer | Yes | Priority value (1 = highest) |
| notes | string | No | Notes |

---

### StudentResponseDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Student ID |
| full_name | string | Yes | Full name |
| status | string | Yes | Current status |
| date_of_birth | date | No | Date of birth |
| gender | string | No | Gender |
| phone | string | No | Phone |
| is_active | boolean | Yes | Active flag |
| waiting_since | datetime | No | Waiting since timestamp |
| waiting_priority | integer | No | Waiting priority |

---

### StudentStatusSummaryDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| active | integer | Yes | Count of active students |
| waiting | integer | Yes | Count of waiting students |
| inactive | integer | Yes | Count of inactive students |
| graduated | integer | Yes | Count of graduated students |

---

### StudentGroupedResultDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| groups | dict | Yes | Grouped data with counts |
| total | integer | Yes | Total count |

---

## Common Response Wrappers

### ApiResponse<T>

```json
{
  "data": T,
  "message": "Optional message",
  "success": true
}
```

### PaginatedResponse<T>

```json
{
  "data": [T],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

---

## Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## Notes

- All datetime fields are in ISO 8601 format (UTC)
- All decimal amounts are returned as numbers (not strings)
- `require_any` = any authenticated user with valid JWT
- `require_admin` = user must have admin role
