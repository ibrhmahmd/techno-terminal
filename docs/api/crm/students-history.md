# CRM Students History & Activity API

Activity tracking and history endpoints for student lifecycle events.

**Base Path:** `/crm`  
**Authentication:** JWT Bearer token required for all endpoints.

---

## Activity Tracking Endpoints

### GET /crm/students/{student_id}/history

Get student activity history (audit log).

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| activity_types | string | No | - | max 100 chars | Comma-separated activity types |
| date_from | datetime | No | - | ISO 8601 | Filter from date |
| date_to | datetime | No | - | ISO 8601 | Filter to date |
| limit | integer | No | 50 | 1-100 | Max records to return |

**Response:** `ApiResponse<List<ActivityLogResponseDTO>>`

```json
{
  "data": [
    {
      "id": 1,
      "student_id": 101,
      "activity_type": "enrollment",
      "activity_subtype": "new",
      "description": "Enrolled in Beginners A",
      "reference_type": "enrollment",
      "reference_id": 25,
      "performed_by_user_id": 5,
      "performed_by_name": "Admin User",
      "created_at": "2024-01-15T10:30:00Z",
      "metadata": {
        "group_id": 5,
        "course_id": 2
      }
    }
  ]
}
```

---

### GET /crm/students/{student_id}/activity-summary

Get activity summary grouped by type.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| date_from | datetime | No | - | ISO 8601 | Filter from date |
| date_to | datetime | No | - | ISO 8601 | Filter to date |

**Response:** `ApiResponse<List<ActivitySummaryItem>>`

```json
{
  "data": [
    {
      "activity_type": "enrollment",
      "count": 3
    },
    {
      "activity_type": "payment",
      "count": 12
    }
  ]
}
```

---

### GET /crm/students/{student_id}/enrollment-history

Get enrollment change history.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| limit | integer | No | 20 | 1-100 | Max records |

**Response:** `ApiResponse<List<EnrollmentHistoryEntry>>`

```json
{
  "data": [
    {
      "enrollment_id": 25,
      "group_name": "Beginners A",
      "course_name": "Intro to Programming",
      "status": "active",
      "enrolled_at": "2024-01-15T10:30:00Z",
      "dropped_at": null
    }
  ]
}
```

---

### POST /crm/students/{student_id}/log-activity

Log a manual activity entry.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | integer | Yes | Student ID |

**Request Body:** `ActivityLogRequest`

```json
{
  "activity_type": "note_added",
  "activity_subtype": "phone_call",
  "description": "Called parent to discuss progress",
  "reference_type": null,
  "reference_id": null
}
```

**Response:** `ApiResponse<ManualActivityResponseDTO>`

```json
{
  "data": {
    "id": 150,
    "student_id": 101,
    "activity_type": "note_added",
    "description": "Called parent to discuss progress",
    "created_at": "2024-01-20T14:30:00Z",
    "performed_by": 5
  },
  "message": "Activity logged successfully"
}
```

---

## Global Activity Endpoints

### GET /crm/history/recent

Get recent activities across all students.

**Authentication:** `require_admin`

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| limit | integer | No | 20 | 1-100 | Max records |
| activity_types | string | No | - | max 100 chars | Filter by types |

**Response:** `ApiResponse<List<RecentActivityItemDTO>>`

```json
{
  "data": [
    {
      "id": 200,
      "student_id": 101,
      "student_name": "John Doe",
      "activity_type": "registration",
      "description": "Student registered",
      "created_at": "2024-01-20T14:30:00Z",
      "performed_by_name": "Admin User"
    }
  ]
}
```

---

### POST /crm/history/search

Search activities with advanced filters.

**Authentication:** `require_any`

**Request Body:** `ActivitySearchParams`

```json
{
  "search_term": "payment",
  "activity_types": ["payment", "enrollment"],
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-31T23:59:59Z",
  "performed_by": 5,
  "student_id": 101,
  "limit": 50
}
```

**Response:** `ApiResponse<List<ActivitySearchResultItemDTO>>`

```json
{
  "data": [
    {
      "id": 195,
      "student_id": 101,
      "student_name": "John Doe",
      "activity_type": "payment",
      "description": "Payment received: $500",
      "created_at": "2024-01-15T10:30:00Z",
      "performed_by_name": "Admin User"
    }
  ]
}
```

---

## Enum Definitions

### ActivityType

Valid activity types for logging and filtering:

| Value | Description |
|-------|-------------|
| `registration` | Student registration |
| `status_change` | Status change (active/waiting/inactive/graduated) |
| `enrollment` | New enrollment |
| `enrollment_change` | Enrollment modification (transfer, drop) |
| `payment` | Payment recorded |
| `note_added` | Manual note or communication |
| `competition` | Competition registration |
| `deletion` | Student deletion |

---

### ReferenceType

Valid reference types for linked entities:

| Value | Description |
|-------|-------------|
| `student` | Student record |
| `enrollment` | Enrollment record |
| `payment` | Payment record |
| `group` | Academic group |
| `course` | Course |
| `competition` | Competition |

---

## Schema Definitions

### ActivityLogResponseDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| activity_type | ActivityType | Yes | Type of activity |
| activity_subtype | string | No | Subtype (max 50 chars) |
| description | string | No | Human-readable description |
| reference_type | ReferenceType | No | Type of referenced entity |
| reference_id | integer | No | ID of referenced entity |
| performed_by_user_id | integer | Yes | User who performed action |
| performed_by_name | string | No | User's name |
| created_at | datetime | Yes | Timestamp |
| metadata | dict | No | Additional JSON data |

---

### ActivitySummaryItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| activity_type | ActivityType | Yes | Activity type |
| count | integer | Yes | Number of activities |

---

### EnrollmentHistoryEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| enrollment_id | integer | Yes | Enrollment ID |
| group_name | string | Yes | Group name |
| course_name | string | Yes | Course name |
| status | string | Yes | Enrollment status |
| enrolled_at | datetime | Yes | Enrollment date |
| dropped_at | datetime | No | Drop date (if dropped) |

---

### ActivityLogRequest

Request body for logging manual activity.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| activity_type | ActivityType | Yes | - | Activity type from enum |
| activity_subtype | string | No | max 50 chars | Subtype classification |
| description | string | No | max 500 chars | Description |
| reference_type | ReferenceType | No | - | Referenced entity type |
| reference_id | integer | No | > 0 | Referenced entity ID |

---

### ActivitySearchParams

Parameters for searching activities.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| search_term | string | No | max 100 chars | Search in description |
| activity_types | List<ActivityType> | No | max 10 items | Filter by types |
| date_from | datetime | No | - | Start date |
| date_to | datetime | No | must be ≥ date_from | End date |
| performed_by | integer | No | > 0 | User ID who performed |
| student_id | integer | No | > 0 | Filter by student |
| limit | integer | No | 1-100, default 50 | Max results |

---

### ManualActivityResponseDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| activity_type | ActivityType | Yes | Activity type |
| description | string | No | Description |
| created_at | datetime | Yes | Timestamp |
| performed_by | integer | Yes | User ID |

---

### RecentActivityItemDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student name |
| activity_type | ActivityType | Yes | Activity type |
| description | string | No | Description |
| created_at | datetime | Yes | Timestamp |
| performed_by_name | string | No | User name |

---

### ActivitySearchResultItemDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student name |
| activity_type | ActivityType | Yes | Activity type |
| description | string | No | Description |
| created_at | datetime | Yes | Timestamp |
| performed_by_name | string | No | User name |

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

- **ActivityType and ReferenceType** are enforced enums - invalid values return 400
- **Date validation:** `date_to` must be ≥ `date_from` if both provided
- **Search limit:** Maximum 100 activities per request
- **Metadata field:** Flexible JSON object for storing additional context
- **Automatic logging:** System automatically logs registration, enrollment, status changes, payments
- **Manual logging:** Use `POST /crm/students/{id}/log-activity` for notes, communications, custom events
