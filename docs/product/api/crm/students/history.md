# Student History & Activity Tracking API

Endpoints for tracking student activities, enrollment history, and audit logging.

**Base Path:** `/api/v1`

---

## Get Student Activity History

Retrieve chronological activity timeline for a specific student.

### Endpoint
```
GET /students/{student_id}/history
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `activity_types` | string | No | null | Comma-separated activity types filter |
| `date_from` | datetime | No | null | Start date (ISO 8601) |
| `date_to` | datetime | No | null | End date (ISO 8601) |
| `limit` | integer | No | 50 | Maximum records (1-500) |
| `offset` | integer | No | 0 | Records to skip |

### Activity Types

Common activity types include:
- `enrollment` - Enrollment changes
- `payment` - Payment transactions
- `group_change` - Group transfers
- `status_change` - Status updates
- `attendance` - Attendance records
- `manual` - Manually logged activities

### Response

**200 OK**
```json
{
  "data": [
    {
      "activity_id": 1,
      "student_id": 1,
      "activity_type": "enrollment",
      "activity_subtype": "enrollment_transfer",
      "description": "Transferred from Group A to Group B",
      "reference": {
        "reference_type": "enrollment",
        "reference_id": 5
      },
      "performed_by": {
        "user_id": 3
      },
      "meta": {
        "previous_group_id": 2,
        "previous_level_number": 1,
        "amount_due": 150.00
      },
      "created_at": "2026-04-09T10:30:00Z"
    }
  ],
  "message": "Retrieved 25 activities",
  "error": null
}
```

### Example Requests

**Get all activities:**
```bash
curl -X GET "https://api.example.com/api/v1/students/1/history" \
  -H "Authorization: Bearer <token>"
```

**Filter by type and date range:**
```bash
curl -X GET "https://api.example.com/api/v1/students/1/history?activity_types=enrollment,payment&date_from=2026-01-01&limit=100" \
  -H "Authorization: Bearer <token>"
```

---

## Get Activity Summary

Get aggregated counts of activities by type for a student.

### Endpoint
```
GET /students/{student_id}/activity-summary
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Response

**200 OK**
```json
{
  "data": [
    {
      "activity_type": "enrollment",
      "count": 5
    },
    {
      "activity_type": "payment",
      "count": 12
    },
    {
      "activity_type": "group_change",
      "count": 2
    }
  ],
  "message": "Activity summary retrieved",
  "error": null
}
```

---

## Get Enrollment History

Retrieve detailed enrollment history including transfers and level changes.

### Endpoint
```
GET /students/{student_id}/enrollment-history
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 50 | Maximum records (1-200) |

### Response

**200 OK**
```json
{
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "enrollment_id": 5,
      "group_id": 3,
      "level_number": 2,
      "action": "transfer",
      "action_date": "2026-03-15T10:30:00Z",
      "previous_group_id": 2,
      "previous_level_number": 1,
      "amount_due": 150.00,
      "amount_paid": 150.00,
      "final_status": "completed",
      "notes": "Level promotion after exam"
    }
  ],
  "message": "Retrieved 3 enrollment history entries",
  "error": null
}
```

---

## Log Manual Activity

Manually log an activity entry for a student (admin only).

### Endpoint
```
POST /students/{student_id}/log-activity
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_type` | string | Yes | Activity category |
| `activity_subtype` | string | No | Specific subtype |
| `reference_type` | string | No | Related entity type |
| `reference_id` | integer | No | Related entity ID |
| `description` | string | Yes | Human-readable description |
| `metadata` | object | No | Additional structured data |

### Example Request
```json
{
  "activity_type": "achievement",
  "activity_subtype": "exam_passed",
  "description": "Passed mid-term exam with distinction",
  "reference_type": "exam",
  "reference_id": 10,
  "metadata": {
    "score": 95,
    "exam_name": "Mid-term Mathematics"
  }
}
```

### Response

**200 OK**
```json
{
  "data": {
    "activity_id": 42,
    "student_id": 1,
    "activity_type": "achievement",
    "description": "Passed mid-term exam with distinction",
    "created_at": "2026-04-09T14:30:00Z"
  },
  "message": "Activity logged successfully",
  "error": null
}
```

---

## Get Recent Activity

Retrieve recent activity across all students (for admin dashboard).

### Endpoint
```
GET /history/recent
```

### Authentication
Any authenticated user (admin/finance roles)

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Maximum records (1-100) |

### Response

**200 OK**
```json
{
  "data": [
    {
      "activity_id": 50,
      "student_id": 3,
      "activity_type": "payment",
      "description": "Payment received: $150.00",
      "created_at": "2026-04-09T15:45:00Z",
      "performed_by_name": "Admin User"
    },
    {
      "activity_id": 49,
      "student_id": 1,
      "activity_type": "enrollment",
      "description": "Enrolled in Group B - Level 2",
      "created_at": "2026-04-09T15:30:00Z",
      "performed_by_name": "Teacher Smith"
    }
  ],
  "message": "Retrieved 20 recent activities",
  "error": null
}
```

---

## Search Activities

Search and filter activities across all students.

### Endpoint
```
POST /history/search
```

### Authentication
Any authenticated user

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `search_term` | string | No | Text to search in descriptions |
| `activity_types` | array | No | Filter by activity types |
| `date_from` | datetime | No | Start date filter |
| `date_to` | datetime | No | End date filter |
| `performed_by` | integer | No | Filter by user who performed action |
| `student_id` | integer | No | Filter by specific student |
| `limit` | integer | No | 50 | Maximum results |

### Example Request
```json
{
  "search_term": "payment",
  "activity_types": ["payment"],
  "date_from": "2026-04-01T00:00:00Z",
  "date_to": "2026-04-30T23:59:59Z",
  "limit": 100
}
```

### Response

**200 OK**
```json
{
  "data": [
    {
      "activity_id": 45,
      "student_id": 2,
      "activity_type": "payment",
      "description": "Payment received: $150.00",
      "meta": {
        "payment_method": "cash",
        "receipt_number": "RCP-2026-0045"
      },
      "created_at": "2026-04-08T10:15:00Z"
    }
  ],
  "message": "Found 25 activities",
  "error": null
}
```

---

## Related Schemas

### ActivityLogResponseDTO
```json
{
  "activity_id": 1,
  "student_id": 1,
  "activity_type": "enrollment",
  "activity_subtype": "enrollment_transfer",
  "description": "Enrollment transfer",
  "reference": {
    "reference_type": "enrollment",
    "reference_id": 5
  },
  "performed_by": {
    "user_id": 3
  },
  "meta": {},
  "created_at": "2026-04-09T10:30:00Z"
}
```

### RecentActivityItemDTO
```json
{
  "activity_id": 50,
  "student_id": 3,
  "activity_type": "payment",
  "description": "Payment received: $150.00",
  "created_at": "2026-04-09T15:45:00Z",
  "performed_by_name": "Admin User"
}
```

### ActivitySearchResultItemDTO
```json
{
  "activity_id": 45,
  "student_id": 2,
  "activity_type": "payment",
  "description": "Payment received",
  "meta": {},
  "created_at": "2026-04-08T10:15:00Z"
}
```

### EnrollmentHistoryEntry
```json
{
  "id": 1,
  "student_id": 1,
  "enrollment_id": 5,
  "group_id": 3,
  "level_number": 2,
  "action": "transfer",
  "action_date": "2026-03-15T10:30:00Z",
  "previous_group_id": 2,
  "previous_level_number": 1,
  "amount_due": 150.00,
  "amount_paid": 150.00,
  "final_status": "completed",
  "notes": "Level promotion"
}
```

### ActivityLogRequest
```json
{
  "activity_type": "achievement",
  "activity_subtype": "exam_passed",
  "reference_type": "exam",
  "reference_id": 10,
  "description": "Passed exam",
  "metadata": {}
}
```

### ActivitySearchParams
```json
{
  "search_term": "payment",
  "activity_types": ["payment", "enrollment"],
  "date_from": "2026-04-01T00:00:00Z",
  "date_to": "2026-04-30T23:59:59Z",
  "performed_by": 3,
  "student_id": 1,
  "limit": 50
}
```

### Supporting DTOs

#### ActivityReferenceDTO
```json
{
  "reference_type": "enrollment",
  "reference_id": 5
}
```

#### ActivityActorDTO
```json
{
  "user_id": 3
}
```

#### ActivitySummaryItem
```json
{
  "activity_type": "enrollment",
  "count": 5
}
```

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
