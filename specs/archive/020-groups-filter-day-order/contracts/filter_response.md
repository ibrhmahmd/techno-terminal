# API Contract: GET /academics/groups/filter — Response

## Success Response (200)

```json
{
  "success": true,
  "data": {
    "groups": [
      {
        "id": 1,
        "name": "Robotics A",
        "default_day": "Saturday",
        "status": "active",
        "capacity": 15,
        "course_id": 3,
        "course_name": "Robotics Engineering",
        "instructor_id": 5,
        "instructor_name": "Ahmed Hassan",
        "level_id": 2,
        "level_name": "Advanced",
        "enrolled_count": 12,
        "schedule": {
          "start_time": "10:00",
          "end_time": "12:00"
        },
        "created_at": "2026-01-15T10:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 50
  },
  "message": "Groups retrieved successfully"
}
```

## Empty Results (200)

```json
{
  "success": true,
  "data": {
    "groups": [],
    "total": 0,
    "skip": 0,
    "limit": 50
  },
  "message": "Groups retrieved successfully"
}
```

## Unauthenticated (401)

```json
{
  "success": false,
  "error": "AuthError",
  "message": "Not authenticated"
}
```
