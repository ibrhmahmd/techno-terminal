# CRM Students Filter API

Flexible student filtering endpoint for advanced search and segmentation.

**Base Path:** `/crm`  
**Router:** `app/api/routers/crm/students_router.py`  
**Authentication:** JWT Bearer token required.

---

## Quick Reference

| Endpoint | Method | Auth | Response |
|----------|--------|------|----------|
| `/students/filter` | GET | `require_any` | `ApiResponse<StudentFilterResultDTO>` |

---

## GET /crm/students/filter

Filter students by multiple criteria including age, status, courses, groups, payment status, and enrollment count.

### Authentication

`require_any` - Any authenticated user with valid JWT.

```http
Authorization: Bearer <access_token>
```

### Query Parameters

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `min_age` | integer | No | - | 0-100 | Minimum student age |
| `max_age` | integer | No | - | 0-100 | Maximum student age |
| `status` | string[] | No | - | active, waiting, inactive | Student statuses (multi-select) |
| `gender` | string[] | No | - | male, female, unknown | Genders (multi-select) |
| `course_ids` | integer[] | No | - | Valid course IDs | Enrolled courses (OR logic) |
| `group_default_day` | string[] | No | - | Monday-Sunday | Group meeting days |
| `instructor_name` | string | No | - | min 1 char | Partial instructor name search |
| `has_unpaid_balance` | boolean | No | - | true/false | Filter by payment status |
| `enrollment_date_from` | date | No | - | YYYY-MM-DD | Enrolled on or after |
| `enrollment_date_to` | date | No | - | YYYY-MM-DD | Enrolled on or before |
| `min_enrollments` | integer | No | - | ≥ 0 | Minimum enrollment count |
| `max_enrollments` | integer | No | - | ≥ 0 | Maximum enrollment count |
| `skip` | integer | No | 0 | ≥ 0 | Pagination offset |
| `limit` | integer | No | 50 | 1-200 | Page size |

### Parameter Examples

**Age range filtering:**
```
?min_age=6&max_age=12
```

**Multiple statuses:**
```
?status=active&status=waiting
```

**Course enrollment (OR logic - student in ANY of these courses):**
```
?course_ids=1,2,5
```

**Multiple group days:**
```
?group_default_day=Saturday&group_default_day=Sunday
```

**Instructor name search:**
```
?instructor_name=Ahmed
```

**Unpaid balance filter:**
```
?has_unpaid_balance=true
```

**Enrollment count range:**
```
?min_enrollments=2&max_enrollments=5
```

**Combined example:**
```
?min_age=8&max_age=14&status=active&course_ids=1,3&has_unpaid_balance=true&limit=25
```

---

## Request / Response Schemas

### Request

No request body required. All parameters are query parameters.

### Response: StudentFilterResultDTO

```json
{
  "data": {
    "students": [
      {
        "id": 1,
        "full_name": "Ahmed Mohamed",
        "age": 10,
        "status": "active",
        "gender": "male",
        "phone": "+20 123 456 7890",
        "current_group_id": 5,
        "current_group_name": "Python Basics - Sat 2PM",
        "group_default_day": "Saturday",
        "instructor_id": 3,
        "instructor_name": "John Smith",
        "enrollment_count": 3,
        "enrolled_courses": [1, 2, 4],
        "unpaid_balance": 1500.00
      }
    ],
    "total": 45,
    "skip": 0,
    "limit": 50
  },
  "message": null,
  "success": true
}
```

### Response Fields

#### StudentFilterItemDTO

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | integer | No | Student ID |
| `full_name` | string | No | Student full name |
| `age` | integer | Yes | Calculated age from date_of_birth |
| `status` | string | No | Student status (active/waiting/inactive) |
| `gender` | string | Yes | Student gender |
| `phone` | string | Yes | Contact phone number |
| `current_group_id` | integer | Yes | Active enrollment group ID |
| `current_group_name` | string | Yes | Active enrollment group name |
| `group_default_day` | string | Yes | Group meeting day |
| `instructor_id` | integer | Yes | Assigned instructor ID |
| `instructor_name` | string | Yes | Assigned instructor name |
| `enrollment_count` | integer | No | Total number of enrollments |
| `enrolled_courses` | integer[] | No | List of enrolled course IDs |
| `unpaid_balance` | float | Yes | Total unpaid balance (null if paid) |

#### StudentFilterResultDTO

| Field | Type | Description |
|-------|------|-------------|
| `students` | StudentFilterItemDTO[] | Filtered student list |
| `total` | integer | Total count (before pagination) |
| `skip` | integer | Current skip value |
| `limit` | integer | Current limit value |

---

## Common Use Cases

### Find students with unpaid balances

```http
GET /api/v1/crm/students/filter?has_unpaid_balance=true
```

### Find active students aged 6-12 in Python course

```http
GET /api/v1/crm/students/filter?min_age=6&max_age=12&status=active&course_ids=1
```

### Find students with multiple enrollments (2-5 courses)

```http
GET /api/v1/crm/students/filter?min_enrollments=2&max_enrollments=5
```

### Find weekend students with specific instructor

```http
GET /api/v1/crm/students/filter?group_default_day=Saturday&group_default_day=Sunday&instructor_name=Ahmed
```

### Find recently enrolled students

```http
GET /api/v1/crm/students/filter?enrollment_date_from=2024-01-01&enrollment_date_to=2024-03-31
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 400 Bad Request

Invalid query parameters:

```json
{
  "detail": "Invalid value for min_age: must be between 0 and 100"
}
```

---

## Implementation Notes

### Filter Logic

- **Age filtering**: Based on `date_of_birth` field, calculated at query time
- **Status/Gender**: Exact match, case-sensitive
- **Course IDs**: OR logic (student enrolled in ANY of the specified courses)
- **Group days**: OR logic (student in group meeting on ANY of the specified days)
- **Instructor name**: Partial case-insensitive match
- **Has unpaid balance**: Checks sum of all enrollment remaining balances > 0
- **Enrollment count**: Counts total enrollments regardless of status
- **Date range**: Filters by `enrolled_at` timestamp

### Performance

- Basic filters (age, status, gender) are applied at database level
- Complex filters (instructor name, course enrollment, balance) are applied in Python
- For large datasets, use specific filters to reduce result set before pagination

---

## Related Endpoints

- [Students API](students.md) - CRUD operations
- [Students Grouped](students.md#get-crmstudentsgrouped) - Group by demographics
- [Student Details](students.md#get-crmstudentsid) - Full student profile
- [Enrollment API](../enrollments.md) - Enrollment management
