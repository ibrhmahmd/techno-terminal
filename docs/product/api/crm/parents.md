# CRM Parents API

Parent management endpoints for the CRM module.

**Base Path:** `/crm`  
**Authentication:** JWT Bearer token required for all endpoints.

---

## CRUD Endpoints

### GET /crm/parents

List and search parents with pagination.

**Authentication:** `require_any`

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| q | string | No | - | min 1, max 100 chars | Search by name or phone |
| skip | integer | No | 0 | ≥ 0 | Pagination offset |
| limit | integer | No | 50 | 1-200 | Page size |

**Response:** `PaginatedResponse<ParentListItem>`

```json
{
  "data": [
    {
      "id": 1,
      "full_name": "Parent Name",
      "phone_primary": "+1234567890"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

**Error Codes:**
- 401: Unauthorized

---

### GET /crm/parents/{parent_id}

Get parent by ID.

**Authentication:** `require_any`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| parent_id | integer | Yes | Parent ID |

**Response:** `ApiResponse<ParentPublic>`

```json
{
  "data": {
    "id": 1,
    "full_name": "Parent Name",
    "phone_primary": "+1234567890",
    "phone_secondary": "+1987654321",
    "email": "parent@example.com",
    "relation": "father",
    "notes": "Primary contact"
  }
}
```

**Error Codes:**
- 404: Parent not found

---

### POST /crm/parents

Create a new parent.

**Authentication:** `require_admin`

**Request Body:** `ParentCreate`

```json
{
  "full_name": "Parent Name",
  "phone_primary": "+1234567890",
  "phone_secondary": "+1987654321",
  "email": "parent@example.com",
  "relation": "mother",
  "notes": "Primary contact for student"
}
```

**Response:** `ApiResponse<ParentPublic>` (201 Created)

```json
{
  "data": {
    "id": 101,
    "full_name": "Parent Name",
    "phone_primary": "+1234567890",
    "phone_secondary": "+1987654321",
    "email": "parent@example.com",
    "relation": "mother",
    "notes": "Primary contact for student"
  }
}
```

**Error Codes:**
- 400: Invalid input data
- 401: Unauthorized

---

### PATCH /crm/parents/{parent_id}

Update parent information.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| parent_id | integer | Yes | Parent ID |

**Request Body:** `ParentUpdate` (all fields optional)

```json
{
  "full_name": "Updated Name",
  "phone_primary": "+1234567890",
  "email": "newemail@example.com"
}
```

**Response:** `ApiResponse<ParentPublic>`

```json
{
  "data": {
    "id": 1,
    "full_name": "Updated Name",
    "phone_primary": "+1234567890",
    "phone_secondary": null,
    "email": "newemail@example.com",
    "relation": "father",
    "notes": "Primary contact"
  }
}
```

**Error Codes:**
- 400: Invalid input
- 404: Parent not found

---

### DELETE /crm/parents/{parent_id}

Delete a parent by ID.

**Authentication:** `require_admin`

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| parent_id | integer | Yes | Parent ID |

**Response:** `ApiResponse<ParentPublic>`

```json
{
  "data": {
    "id": 1,
    "full_name": "Parent Name",
    "phone_primary": "+1234567890"
  }
}
```

**Error Codes:**
- 404: Parent not found

---

## Schema Definitions

### ParentPublic

Full parent profile returned by GET endpoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Parent ID |
| full_name | string | Yes | Full name |
| phone_primary | string | Yes | Primary phone number |
| phone_secondary | string | No | Secondary phone number |
| email | string | No | Email address |
| relation | string | No | Relationship (father, mother, guardian, etc.) |
| notes | string | No | Additional notes |

---

### ParentListItem

Slim representation for list responses.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Parent ID |
| full_name | string | Yes | Full name |
| phone_primary | string | Yes | Primary phone number |

---

### ParentCreate

Input for creating a new parent.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| full_name | string | Yes | - | Full name |
| phone_primary | string | Yes | - | Primary phone number |
| phone_secondary | string | No | - | Secondary phone |
| email | string | No | valid email | Email address |
| relation | string | No | - | Relationship to student |
| notes | string | No | - | Additional notes |

---

### ParentUpdate

Input for updating an existing parent. All fields optional.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| full_name | string | No | Full name |
| phone_primary | string | No | Primary phone |
| phone_secondary | string | No | Secondary phone |
| email | string | No | Email address |
| relation | string | No | Relationship |
| notes | string | No | Notes |

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
  "status_code": 404
}
```

---

## Notes

- **Phone format:** Any valid phone number format accepted
- **Email validation:** Standard email format validation applied
- **Relation field:** Free text - common values: `father`, `mother`, `guardian`, `grandparent`
- **Search:** Parent search matches against both `full_name` and `phone_primary`
- **Linked students:** To get students linked to a parent, use `GET /crm/students/{student_id}/parents` or check the parent's student list in the CRM interface
