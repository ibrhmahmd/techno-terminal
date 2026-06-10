# API Contract: POST /api/v1/crm/students

## Endpoint
```
POST /api/v1/crm/students
Authorization: Bearer <jwt>
Content-Type: application/json
```

## Request Body

### RegisterStudentCommandDTO

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `student_data` | `RegisterStudentDTO` | **Yes** | — | Nested student payload |
| `parent_id` | `int \| null` | No | `null` | Existing parent ID to link |
| `relationship` | `string \| null` | No | `null` | e.g., "father", "mother" |
| `created_by_user_id` | `int \| null` | No | Current user | Override audit user |

### RegisterStudentDTO (inside `student_data`)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `full_name` | `string` | **Yes** | — | Student's full name |
| `date_of_birth` | `date (ISO 8601) \| null` | No | `null` | YYYY-MM-DD |
| `gender` | `string \| null` | No | `null` | `"male"` or `"female"` |
| `phone` | `string \| null` | No | `null` | Contact phone |
| `notes` | `string \| null` | No | `null` | Free-text notes |
| `status` | `string \| null` | No | `"waiting"` | **Case-insensitive** — one of: `"active"`, `"waiting"`, `"inactive"` |

### Status Field Validation Rules (Post-Fix)

1. If `null` or omitted → defaults to `"waiting"` in the service layer
2. If a string → **lowercased before enum validation** via `@field_validator(mode="before")`
3. After lowercasing → must be one of: `"active"`, `"waiting"`, `"inactive"`
4. If none of the above → **422 ValidationError** with details

### Example Request (status="waiting")

```json
{
  "student_data": {
    "full_name": "Ahmed Mohamed",
    "date_of_birth": "2012-05-15",
    "gender": "male",
    "phone": "+201234567890",
    "notes": "New student",
    "status": "waiting"
  },
  "parent_id": null,
  "relationship": null,
  "created_by_user_id": null
}
```

### Example Request (status omitted — default)

```json
{
  "student_data": {
    "full_name": "Sara Ali",
    "date_of_birth": "2011-08-22",
    "gender": "female",
    "phone": "+201098765432",
    "notes": ""
  },
  "parent_id": 5,
  "relationship": "mother",
  "created_by_user_id": null
}
```

### Example Request (case variation — capitalized)

```json
{
  "student_data": {
    "full_name": "Omar Hassan",
    "status": "Waiting"
  },
  "parent_id": null,
  "relationship": null,
  "created_by_user_id": null
}
```

**Note**: `"Waiting"` (capitalized) is normalized to `"waiting"` by the validator.

## Response

### 201 Created — Success

```json
{
  "success": true,
  "data": {
    "id": 42,
    "full_name": "Ahmed Mohamed",
    "date_of_birth": "2012-05-15",
    "gender": "male",
    "phone": "+201234567890",
    "status": "waiting",
    "notes": "New student"
  },
  "message": "Student registered successfully."
}
```

### 422 Validation Error — Invalid Status

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "('body', 'student_data', 'status'): Input should be 'active', 'waiting' or 'inactive'",
  "details": [
    {
      "input": "pending",
      "loc": ["body", "student_data", "status"],
      "msg": "Input should be 'active', 'waiting' or 'inactive'",
      "type": "enum",
      "url": "https://errors.pydantic.dev/.../enum"
    }
  ]
}
```

### 409 Conflict — Duplicate Student

```json
{
  "success": false,
  "error": "ConflictError",
  "message": "Student with name 'Ahmed Mohamed' and date of birth '2012-05-15' already exists."
}
```
