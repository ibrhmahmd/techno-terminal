# Academics API - Courses Router

Router source: `app/api/routers/academics/courses.py`  
Mounted prefix: `/api/v1`  
Router base paths: `/academics/courses`, `/academics/courses/{course_id}`, `/academics/courses/{course_id}/price`, `/academics/courses/stats`, `/academics/courses/{course_id}/stats`, `/academics/courses/{course_id}/groups`

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

Common auth errors:
- `401 Unauthorized` - missing/invalid token
- `403 Forbidden` - inactive user or insufficient role

---

## DTOs and Schemas

### Request DTOs

#### AddNewCourseInput
```json
{
  "name": "Robotics Fundamentals",
  "category": "STEM",
  "description": "Introduction to robotics",
  "notes": "Beginner track",
  "price_per_level": 1500.0,
  "sessions_per_level": 12
}
```

Validation:
- `name` required
- `price_per_level` required, must be `> 0`
- `sessions_per_level` required, must be `>= 1`

#### UpdateCourseDTO
```json
{
  "name": "Robotics Fundamentals - Updated",
  "category": "STEM",
  "description": "Updated description",
  "notes": "Updated notes",
  "price_per_level": 1600.0,
  "sessions_per_level": 14,
  "is_active": true
}
```

Validation:
- all fields optional
- if provided, `price_per_level` must be `> 0`
- if provided, `sessions_per_level` must be `>= 1`

#### UpdateCoursePriceInput
```json
{
  "new_price": 1750.0
}
```

Validation:
- `new_price` required, must be `> 0`

### Response DTOs

#### CoursePublic
```json
{
  "id": 1,
  "name": "Robotics Fundamentals",
  "category": "STEM",
  "description": "Introduction to robotics",
  "price_per_level": 1500.0,
  "sessions_per_level": 12,
  "is_active": true
}
```

#### CourseStatsPublic
```json
{
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "total_groups": 5,
  "active_groups": 3,
  "total_students_ever": 120,
  "active_students": 45
}
```

#### EnrichedGroupPublic (used by course groups endpoint)
```json
{
  "id": 10,
  "name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "instructor_id": 7,
  "instructor_name": "Ahmed Hassan",
  "level_number": 1,
  "max_capacity": 15,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "default_time_end": "16:00:00",
  "is_active": true
}
```

### Envelopes

#### ApiResponse<T>
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

#### PaginatedResponse<T>
```json
{
  "success": true,
  "data": [],
  "total": 0,
  "skip": 0,
  "limit": 50
}
```

#### ErrorResponse
```json
{
  "success": false,
  "error": "NotFoundError",
  "message": "Course 999 not found."
}
```

---

## Endpoints

### 1) List all active courses
**GET** `/api/v1/academics/courses`  
Auth: `require_any`

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<CoursePublic>`

Errors:
- `401`, `403`, `422`

Example response:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Robotics Fundamentals",
      "category": "STEM",
      "description": "Introduction to robotics",
      "price_per_level": 1500.0,
      "sessions_per_level": 12,
      "is_active": true
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

### 2) Create a new course
**POST** `/api/v1/academics/courses`  
Auth: `require_admin`

Request body:
- `AddNewCourseInput`

Response:
- `201 Created` -> `ApiResponse<CoursePublic>`

Errors:
- `401`, `403`, `409`, `422`

Example request:
```json
{
  "name": "AI Foundations",
  "category": "STEM",
  "description": "Intro to AI concepts",
  "notes": "Starts next month",
  "price_per_level": 1800.0,
  "sessions_per_level": 10
}
```

### 3) Get a course by ID
**GET** `/api/v1/academics/courses/{course_id}`  
Auth: `require_any`

Path params:
- `course_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<CoursePublic>`

Errors:
- `401`, `403`, `404`, `422`

### 4) Soft delete a course
**DELETE** `/api/v1/academics/courses/{course_id}`  
Auth: `require_admin`

Path params:
- `course_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<CoursePublic>`

Errors:
- `401`, `403`, `404`, `422`

Example response:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "AI Foundations",
    "category": "STEM",
    "description": "Intro to AI concepts",
    "price_per_level": 1800.0,
    "sessions_per_level": 10,
    "is_active": false
  },
  "message": "Course archived successfully."
}
```

### 5) Update a course
**PATCH** `/api/v1/academics/courses/{course_id}`  
Auth: `require_admin`

Path params:
- `course_id` (integer, required)

Request body:
- `UpdateCourseDTO`

Response:
- `200 OK` -> `ApiResponse<CoursePublic>`

Errors:
- `401`, `403`, `404`, `422`

### 6) Update course price
**PATCH** `/api/v1/academics/courses/{course_id}/price`  
Auth: `require_admin`

Path params:
- `course_id` (integer, required)

Request body:
- `UpdateCoursePriceInput`

Response:
- `200 OK` -> `ApiResponse<CoursePublic>`

Errors:
- `401`, `403`, `404`, `422`

### 7) Get aggregate stats for all courses
**GET** `/api/v1/academics/courses/stats`  
Auth: `require_any`

Response:
- `200 OK` -> `ApiResponse<list<CourseStatsPublic>>`

Errors:
- `401`, `403`

### 8) Get aggregate stats for a single course
**GET** `/api/v1/academics/courses/{course_id}/stats`  
Auth: `require_any`

Path params:
- `course_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<CourseStatsPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 9) Get all groups for a specific course
**GET** `/api/v1/academics/courses/{course_id}/groups`  
Auth: `require_any`

Path params:
- `course_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<list<EnrichedGroupPublic>>`

Errors:
- `401`, `403`, `422`

---

## Router Notes

- This router currently exposes **9 endpoints**.
- Course stats endpoints use service-level aggregation from the `v_course_stats` view.
- Soft delete is implemented by setting `is_active = false` (not hard delete).
