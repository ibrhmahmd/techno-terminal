# Student Status & Enrollment Management API

Endpoints for managing student enrollment status, waiting lists, and priority management.

**Base Path:** `/api/v1/crm`

---

## Status Overview

Students can have the following enrollment statuses:

| Status | Description |
|--------|-------------|
| `active` | Currently enrolled in classes |
| `waiting` | On waiting list for enrollment |
| `inactive` | Temporarily or permanently inactive |
| `graduated` | Completed program |

---

## Update Student Status

Change a student's enrollment status with optional audit notes.

### Endpoint
```
PATCH /crm/students/{student_id}/status
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
| `status` | string | Yes | New status: "active", "waiting", "inactive", "graduated" |
| `notes` | string | No | Audit notes explaining the change |

### Example Request
```json
{
  "status": "active",
  "notes": "Completed waiting period, assigned to group A"
}
```

### Response

**200 OK**
```json
{
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "status": "active",
    "status_updated_at": "2026-04-09T10:30:00Z"
  },
  "message": "Student status updated to active",
  "error": null
}
```

**400 Bad Request** - Invalid status
```json
{
  "data": null,
  "message": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid status value"
  }
}
```

**404 Not Found**
```json
{
  "data": null,
  "message": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Student 123 not found"
  }
}
```

---

## Toggle Student Status

Quick endpoint to toggle between `active` and `waiting` statuses.

### Endpoint
```
POST /crm/students/{student_id}/status/toggle
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notes` | string | No | Audit notes for the toggle |

### Example Request
```bash
curl -X POST "https://api.example.com/api/v1/crm/students/1/status/toggle?notes=Moved to waiting list" \
  -H "Authorization: Bearer <token>"
```

### Response

**200 OK** - Toggled from active to waiting
```json
{
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "status": "waiting",
    "waiting_since": "2026-04-09T10:30:00Z"
  },
  "message": "Student status toggled to waiting",
  "error": null
}
```

---

## Get Waiting List

Retrieve all students currently on the waiting list.

### Endpoint
```
GET /crm/students/waiting-list
```

### Authentication
Admin only

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 200 | Maximum records to return |
| `order_by_priority` | boolean | No | true | Sort by priority (1=highest) |

### Response

**200 OK**
```json
{
  "data": [
    {
      "id": 2,
      "full_name": "Jane Smith",
      "status": "waiting",
      "waiting_since": "2026-01-15T08:00:00Z",
      "waiting_priority": 1,
      "phone": "+1987654321"
    },
    {
      "id": 3,
      "full_name": "Bob Wilson",
      "status": "waiting",
      "waiting_since": "2026-02-01T09:00:00Z",
      "waiting_priority": 2,
      "phone": "+1555666777"
    }
  ],
  "message": "Retrieved 2 students from waiting list",
  "error": null
}
```

---

## Set Waiting Priority

Adjust priority for a student on the waiting list (1 = highest priority).

### Endpoint
```
PATCH /crm/students/{student_id}/waiting-priority
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
| `priority` | integer | Yes | Priority level (1-100, 1=highest) |

### Example Request
```json
{
  "priority": 1
}
```

### Response

**200 OK**
```json
{
  "data": {
    "id": 2,
    "full_name": "Jane Smith",
    "status": "waiting",
    "waiting_priority": 1
  },
  "message": "Waiting priority set to 1",
  "error": null
}
```

**404 Not Found** - Student not on waiting list
```json
{
  "data": null,
  "message": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Student 123 not found or not on waiting list"
  }
}
```

---

## Get Students by Status

Filter students by their enrollment status.

### Endpoint
```
GET /crm/students/by-status/{status}
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Status filter: "active", "waiting", "inactive", "graduated" |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 200 | Maximum records to return |

### Example Request
```bash
curl -X GET "https://api.example.com/api/v1/crm/students/by-status/waiting?limit=50" \
  -H "Authorization: Bearer <token>"
```

### Response

**200 OK**
```json
{
  "data": [
    {
      "id": 2,
      "full_name": "Jane Smith",
      "status": "waiting",
      "waiting_since": "2026-01-15T08:00:00Z"
    }
  ],
  "message": "Retrieved 1 waiting students",
  "error": null
}
```

**400 Bad Request** - Invalid status
```json
{
  "data": null,
  "message": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid status: unknown"
  }
}
```

---

## Get Status Summary

Get counts of students grouped by enrollment status.

### Endpoint
```
GET /crm/students/status-summary
```

### Authentication
Admin only

### Response

**200 OK**
```json
{
  "data": {
    "active": 145,
    "waiting": 23,
    "inactive": 12,
    "graduated": 89,
    "total": 269
  },
  "message": null,
  "error": null
}
```

---

## Get Status History

Retrieve audit log of all status changes for a student.

### Endpoint
```
GET /crm/students/{student_id}/status-history
```

### Authentication
Admin only

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
      "id": 1,
      "student_id": 1,
      "previous_status": "waiting",
      "new_status": "active",
      "changed_at": "2026-03-15T10:30:00Z",
      "changed_by": 5,
      "notes": "Completed waiting period"
    },
    {
      "id": 2,
      "student_id": 1,
      "previous_status": null,
      "new_status": "waiting",
      "changed_at": "2026-01-10T14:00:00Z",
      "changed_by": 3,
      "notes": "Initial registration"
    }
  ],
  "message": null,
  "error": null
}
```

**404 Not Found**
```json
{
  "data": null,
  "message": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Student 123 not found"
  }
}
```

---

## Related Schemas

### StudentStatus Enum
```typescript
type StudentStatus = "active" | "waiting" | "inactive" | "graduated";
```

### UpdateStudentStatusDTO
```json
{
  "status": "active",
  "notes": "Optional audit notes"
}
```

### SetWaitingPriorityDTO
```json
{
  "priority": 1
}
```

### StudentStatusSummaryDTO
```json
{
  "active": 145,
  "waiting": 23,
  "inactive": 12,
  "graduated": 89,
  "total": 269
}
```

### StudentResponseDTO
```json
{
  "id": 1,
  "full_name": "John Doe",
  "status": "active",
  "waiting_since": null,
  "waiting_priority": null,
  "is_active": true
}
```

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
