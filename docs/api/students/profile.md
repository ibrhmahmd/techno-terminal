# Student Profile Management API

Endpoints for student CRUD operations, registration, and parent linking.

**Base Path:** `/api/v1/crm`

---

## List Students

Retrieve a paginated list of students or search by name/phone.

### Endpoint
```
GET /crm/students
```

### Authentication
Any authenticated user

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | No | "" | Search query (min 2 characters). Empty returns all. |
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 50 | Records per page (1-200) |

### Response

**200 OK**
```json
{
  "data": [
    {
      "id": 1,
      "full_name": "John Doe",
      "phone": "+1234567890",
      "is_active": true,
      "notes": "New student",
      "current_group_id": 5,
      "current_group_name": "Math Level 1"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

### Example Requests

**List all students (paginated):**
```bash
curl -X GET "https://api.example.com/api/v1/crm/students?skip=0&limit=20" \
  -H "Authorization: Bearer <token>"
```

**Search students:**
```bash
curl -X GET "https://api.example.com/api/v1/crm/students?q=john" \
  -H "Authorization: Bearer <token>"
```

---

## Get Student by ID

Retrieve complete student profile details.

### Endpoint
```
GET /crm/students/{student_id}
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
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "date_of_birth": "2010-05-15",
    "gender": "male",
    "phone": "+1234567890",
    "is_active": true,
    "notes": "Math enthusiast"
  },
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
    "message": "Student not found"
  }
}
```

---

## Register New Student

Create a new student profile and optionally link to a parent.

### Endpoint
```
POST /crm/students
```

### Authentication
Admin only

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_data` | object | Yes | Student profile data |
| `student_data.full_name` | string | Yes | Student's full name |
| `student_data.date_of_birth` | date | No | Date of birth (ISO 8601) |
| `student_data.gender` | string | No | "male", "female", or "other" |
| `student_data.phone` | string | No | Contact phone number |
| `student_data.notes` | string | No | Additional notes |
| `parent_id` | integer | No | ID of existing parent to link |
| `relationship` | string | No | Relationship to parent (e.g., "father", "mother") |
| `created_by_user_id` | integer | Yes | User ID creating the record |

### Example Request
```json
{
  "student_data": {
    "full_name": "Jane Smith",
    "date_of_birth": "2012-03-20",
    "gender": "female",
    "phone": "+1987654321",
    "notes": "Sibling of John Doe"
  },
  "parent_id": 5,
  "relationship": "mother",
  "created_by_user_id": 1
}
```

### Response

**201 Created**
```json
{
  "data": {
    "id": 2,
    "full_name": "Jane Smith",
    "date_of_birth": "2012-03-20",
    "gender": "female",
    "phone": "+1987654321",
    "is_active": true,
    "notes": "Sibling of John Doe"
  },
  "message": "Student registered successfully.",
  "error": null
}
```

---

## Update Student Profile

Modify existing student information.

### Endpoint
```
PATCH /crm/students/{student_id}
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Request Body

All fields optional - only provided fields will be updated:

| Field | Type | Description |
|-------|------|-------------|
| `full_name` | string | Student's full name |
| `date_of_birth` | date | Date of birth (ISO 8601) |
| `gender` | string | "male", "female", or "other" |
| `phone` | string | Contact phone number |
| `notes` | string | Additional notes |

### Example Request
```json
{
  "phone": "+1111222333",
  "notes": "Updated contact information"
}
```

### Response

**200 OK**
```json
{
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "date_of_birth": "2010-05-15",
    "gender": "male",
    "phone": "+1111222333",
    "is_active": true,
    "notes": "Updated contact information"
  },
  "message": null,
  "error": null
}
```

---

## Delete Student

Remove a student from the system.

### Endpoint
```
DELETE /crm/students/{student_id}
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
  "data": null,
  "message": "Student deleted successfully.",
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

## Get Student Parents

Retrieve all parents linked to a student.

### Endpoint
```
GET /crm/students/{student_id}/parents
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
      "id": 5,
      "full_name": "Mary Smith",
      "phone": "+1987654321",
      "email": "mary@example.com",
      "relationship": "mother"
    }
  ],
  "message": null,
  "error": null
}
```

---

## Related Schemas

### StudentPublic
Full student profile returned by detail endpoints.

```json
{
  "id": 1,
  "full_name": "John Doe",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "+1234567890",
  "is_active": true,
  "notes": "Math enthusiast"
}
```

### StudentListItem
Slim representation for list views.

```json
{
  "id": 1,
  "full_name": "John Doe",
  "phone": "+1234567890",
  "is_active": true,
  "notes": null,
  "current_group_id": 5,
  "current_group_name": "Math Level 1"
}
```

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
