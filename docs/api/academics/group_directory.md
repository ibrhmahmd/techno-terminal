# Academics API - Group Directory Router

Router source: `app/api/routers/academics/group_directory_router.py`

Mounted prefix: `/api/v1`

---

## Related Documentation

This file documents the **Group Directory Router**, responsible for listing, searching, filtering, and grouping. For related endpoints, see:

- **Groups Core Router**: [groups.md](groups.md) - Group scheduling, updating, archiving, level progression
- **Group Lifecycle Router**: [group_lifecycle.md](group_lifecycle.md) - Level management, history, analytics
- **Group Competitions Router**: [group_competitions.md](group_competitions.md) - Teams and competition participation

---

## Authentication & Authorization

All endpoints in this router are read-only and require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_any`: any authenticated active user

Common auth errors:
- `401 Unauthorized`
- `403 Forbidden`

---

## DTOs and Schemas

### Response DTOs

#### GroupListItem
```json
{
  "id": 10,
  "name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "level_number": 1,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "status": "active"
}
```

#### EnrichedGroupPublic
```json
{
  "id": 10,
  "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
  "course_id": 1,
  "course_name": "Robotics Fundamentals",
  "instructor_id": 7,
  "instructor_name": "Ahmed Hassan",
  "level_number": 1,
  "max_capacity": 15,
  "default_day": "Saturday",
  "default_time_start": "14:00:00",
  "default_time_end": "16:00:00",
  "notes": "Weekend batch",
  "status": "active",
  "current_student_count": 12
}
```

#### GroupedGroupsResponse
```json
{
  "groups": [
    {
      "key": "saturday",
      "label": "Saturday",
      "count": 5,
      "groups": [
        {
          "id": 10,
          "group_name": "Saturday 2:00 PM - Robotics Fundamentals",
          "course_name": "Robotics Fundamentals",
          "instructor_name": "Ahmed Hassan",
          "...": "..."
        }
      ]
    }
  ],
  "total": 7,
  "group_by": "day"
}
```

Fields:
- `groups`: array of grouped items
- `key`: grouping key (e.g., "saturday", "1", "active")
- `label`: display label (e.g., "Saturday", "Robotics Fundamentals", "Active")
- `count`: number of groups in this category
- `groups`: array of `EnrichedGroupPublic`
- `total`: total number of groups across all categories
- `group_by`: the field used for grouping

---

## Endpoints

### 1) List all active groups
**GET** `/api/v1/academics/groups`  
Auth: `require_any`

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `422`

### 2) Get all active enriched groups
**GET** `/api/v1/academics/groups/enriched`  
Auth: `require_any`

Response:
- `200 OK` -> `ApiResponse<list<EnrichedGroupPublic>>`

Errors:
- `401`, `403`

### 3) Get archived groups (paginated)
**GET** `/api/v1/academics/groups/archived`  
Auth: `require_any`

Query:
- `skip` (optional, default `0`, `>= 0`)
- `limit` (optional, default `50`, `>= 1`, `<= 200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `422`

### 4) Search groups by name
**GET** `/api/v1/academics/groups/search`  
Auth: `require_any`

Query:
- `query` (required, min length 2): Search string
- `status` (optional): Filter by status
- `skip` (optional, default `0`)
- `limit` (optional, default `20`, max `100`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `422`

### 5) Get groups grouped by field
**GET** `/api/v1/academics/groups/grouped`  
Auth: `require_any`

Query:
- `group_by` (required): Field to group by - one of `day`, `course`, `instructor`, `status`
- `skip` (optional, default `0`, `>= 0`): Pagination offset
- `limit` (optional, default `50`, `>= 1`, `<= 200`): Page size
- `search` (optional): Search term to filter groups by name/course/instructor

Response:
- `200 OK` -> `ApiResponse<GroupedGroupsResponse>`

Errors:
- `401`, `403`, `422`

Notes:
- Groups are organized by the specified field for easier navigation.
- Supports pagination at the group level.
- Search filters groups before grouping.

### 6) Get groups by course
**GET** `/api/v1/academics/groups/by-course/{course_id}`  
Auth: `require_any`

Path params:
- `course_id` (integer, required, > 0)

Query:
- `include_inactive` (optional, default `false`)
- `level_number` (optional, > 0): Filter by level
- `skip` (optional, default `0`)
- `limit` (optional, default `50`, max `200`)

Response:
- `200 OK` -> `PaginatedResponse<EnrichedGroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

### 7) List groups by type
**GET** `/api/v1/academics/groups/by-type/{group_type}`  
Auth: `require_any`

Path params:
- `group_type` (string, required)

Query:
- `status` (optional): Filter by status
- `skip` (optional, default `0`)
- `limit` (optional, default `50`, max `200`)

Response:
- `200 OK` -> `PaginatedResponse<GroupListItem>`

Errors:
- `401`, `403`, `404`, `422`

### 8) Get enriched group by ID
**GET** `/api/v1/academics/groups/{group_id}/enriched`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<EnrichedGroupPublic>`

Errors:
- `401`, `403`, `404`, `422`

---

## Router Notes

- The Group Directory router exposes **8 endpoints** for group listings and searches.
- All endpoints are strictly read-only (`require_any`).
- Separates complex querying (like `/grouped`) from basic core CRUD operations.
