# API Contracts: Group Level Management

**Feature**: 037-group-level-management  
**Date**: 2026-07-10

---

## Endpoint 1: `DELETE /academics/groups/{group_id}/levels/{level_number}`

**Purpose**: Undo the progression of the latest level.

### Response Shape (Success: 200 OK)

```json
{
  "success": true,
  "data": {
    "level_number_deleted": 3,
    "reverted_to_level": 2,
    "sessions_deleted": 5,
    "enrollments_deleted": 12,
    "enrollments_reactivated": 12,
    "group_level_number_after": 2
  },
  "message": "Level 3 deleted successfully. Group reverted to Level 2."
}
```

### Response Shape (Blocked: 409 Conflict)

If the level cannot be deleted due to payment or attendance records:

```json
{
  "success": false,
  "error": "ConflictError",
  "message": "Cannot delete level 3: it has 5 payments and 12 attendance records. Use cancel level instead."
}
```

---

## Endpoint 2: `PATCH /academics/groups/{group_id}/levels/{level_number}`

**Purpose**: Partial update of a group level's details.

### Request Shape

```json
{
  "instructor_id": 5,
  "course_id": 3,
  "price_override": 350.00,
  "notes": "Instructor changed mid-semester"
}
```

*All fields are optional.*

### Response Shape (Success: 200 OK)

```json
{
  "success": true,
  "data": {
    "id": 42,
    "group_id": 10,
    "level_number": 2,
    "course_id": 3,
    "course_name": "EV3",
    "instructor_id": 5,
    "instructor_name": "Mariam Tawfik",
    "sessions_planned": 5,
    "price_override": 350.00,
    "status": "active",
    "effective_from": "2026-07-01T00:00:00Z",
    "effective_to": null,
    "created_at": "2026-07-01T00:00:00Z"
  },
  "message": "Level 2 updated successfully."
}
```

---

## Removed / Deprecated Endpoints

| Endpoint | Method | Action | Rationale |
|---|---|---|---|
| `/academics/groups/{group_id}/levels/{level_number}/complete` | `POST` | **Removed** | Nonexistent method in service; progression is handled via `/academics/groups/{id}/progress-level` |
