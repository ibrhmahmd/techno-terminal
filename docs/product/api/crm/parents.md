# CRM API - Parents Router

Router source: `app/api/routers/crm/parents.py`  
Mounted prefix: `/api/v1`  
Router prefix: `/crm`

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

Common auth errors:
- `401 Unauthorized`
- `403 Forbidden`

---

## DTOs and Schemas

### Request DTOs

#### RegisterParentInput
```json
{
  "full_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "phone_secondary": "01234567890",
  "email": "ahmed@example.com",
  "relation": "Father",
  "notes": "Primary contact for Omar"
}
```

Validation:
- `full_name` required
- `phone_primary` required
- `phone_primary` is normalized to digits and must contain at least 10 digits

#### UpdateParentDTO
```json
{
  "full_name": "Ahmed Mohamed Updated",
  "phone_primary": "01123456789",
  "phone_secondary": "01234567890",
  "email": "ahmed.updated@example.com",
  "relation": "Father",
  "notes": "Updated notes"
}
```

Validation:
- all fields optional
- no custom validator is defined in this DTO

#### FindOrCreateParentInput
```json
{
  "full_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "phone_secondary": "01234567890",
  "email": "ahmed@example.com",
  "relation": "Father",
  "notes": "Primary contact for Omar"
}
```

Validation:
- `full_name` required
- `phone_primary` required, normalized, minimum 10 digits

### Response DTOs

#### ParentPublic
```json
{
  "id": 1,
  "full_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "phone_secondary": "01234567890",
  "email": "ahmed@example.com",
  "relation": "Father",
  "notes": "Primary contact for Omar"
}
```

#### ParentListItem
```json
{
  "id": 1,
  "full_name": "Ahmed Mohamed",
  "phone_primary": "01123456789"
}
```

#### FindOrCreateParentResponse
```json
{
  "data": {
    "id": 1,
    "full_name": "Ahmed Mohamed",
    "phone_primary": "01123456789",
    "phone_secondary": "01234567890",
    "email": "ahmed@example.com",
    "relation": "Father",
    "notes": "Primary contact for Omar"
  },
  "created": true,
  "message": "Parent created successfully."
}
```

#### StudentPublic (used by parent-students endpoint)
```json
{
  "id": 10,
  "full_name": "Omar Mohamed",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "01123456789",
  "is_active": true,
  "notes": "Allergic to peanuts"
}
```

---

## Endpoints

### 1) List / search parents
**GET** `/api/v1/crm/parents`  
Auth: `require_any`

Query:
- `q` (optional string, default `""`; search applied only when trimmed length >= 2)
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<ParentListItem>`

Errors:
- `401`, `403`, `422`

### 2) Get parent by ID
**GET** `/api/v1/crm/parents/{parent_id}`  
Auth: `require_any`

Path params:
- `parent_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<ParentPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 3) Register a new parent
**POST** `/api/v1/crm/parents`  
Auth: `require_admin`

Request body:
- `RegisterParentInput`

Response:
- `201 Created` -> `ApiResponse<ParentPublic>`

Errors:
- `401`, `403`, `409`, `422`

`409` occurs when `phone_primary` already exists.

### 4) Update parent profile
**PATCH** `/api/v1/crm/parents/{parent_id}`  
Auth: `require_admin`

Path params:
- `parent_id` (integer, required)

Request body:
- `UpdateParentDTO`

Response:
- `200 OK` -> `ApiResponse<ParentPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 5) Find existing parent by phone or create new
**POST** `/api/v1/crm/parents/find-or-create`  
Auth: `require_admin`

Request body:
- `FindOrCreateParentInput`

Response:
- `201 Created` -> `FindOrCreateParentResponse`

Errors:
- `401`, `403`, `422`

Notes:
- Returns `created: false` when a parent already exists by `phone_primary`
- Returns `created: true` and creates a record otherwise

### 6) Get all students linked to a parent
**GET** `/api/v1/crm/parents/{parent_id}/students`  
Auth: `require_any`

Path params:
- `parent_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<StudentPublic>>`

Errors:
- `401`, `403`, `404`, `422`

### 7) Delete parent (soft delete)
**DELETE** `/api/v1/crm/parents/{parent_id}`  
Auth: `require_admin`

Path params:
- `parent_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<None>`

Errors:
- `401`, `403`, `404`, `422`

Example success response:
```json
{
  "success": true,
  "data": null,
  "message": "Parent deleted successfully."
}
```

---

## Router Notes

- This router exposes **7 endpoint signatures**.
- Parent delete is soft-delete behavior in service (`is_active = false`).
