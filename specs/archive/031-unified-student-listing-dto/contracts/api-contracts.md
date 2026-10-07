# API Contracts: Unified Student Listing DTO

**Feature**: 031-unified-student-listing-dto  
**Date**: 2026-06-10

All five endpoints continue to use the existing `ApiResponse<T>` / `PaginatedResponse<T>` envelopes. Only the item shape changes.

---

## Common Response Item: `StudentListingDTO`

All five endpoints return items of this shape (as the core). Some endpoints extend it with additional fields.

```json
{
  "id": 42,
  "full_name": "Ahmed Hassan",
  "status": "active",
  "phone": "01012345678",
  "date_of_birth": "2012-03-15",
  "age": 14,
  "gender": "male",
  "current_group_name": "Level 2 - Saturday",
  "has_unpaid_balance": true
}
```

**Nullable fields**: `phone`, `date_of_birth`, `age`, `gender`, `current_group_name`  
**Always present**: `id`, `full_name`, `status`, `has_unpaid_balance`

---

## Endpoint 1: `GET /crm/students`

**Change**: Paginated response item type promoted from `StudentListItem` to `StudentListingDTO`.  
**New fields on each item**: `date_of_birth`, `age`, `gender` (was present in DB, now included), `has_unpaid_balance`.  
**Envelope**: `PaginatedResponse<StudentListingDTO>` (unchanged structure)

```json
{
  "success": true,
  "data": [ { ...StudentListingDTO... } ],
  "total": 120,
  "skip": 0,
  "limit": 50
}
```

---

## Endpoint 2: `GET /crm/students?q={query}`

**Change**: Search result item promoted to `StudentListingDTO`. Adds `age` (previously missing).  
**Envelope**: `PaginatedResponse<StudentListingDTO>` (unchanged)

---

## Endpoint 3: `GET /crm/students/grouped`

**Change**: Student objects inside each bucket promoted to `StudentListingDTO`. Adds `age`, `has_unpaid_balance`.  
**Envelope**: `ApiResponse<StudentGroupedResultDTO>` (unchanged outer structure)

```json
{
  "success": true,
  "data": {
    "group_by": "status",
    "total_unique_students": 95,
    "total": 95,
    "groups": [
      {
        "key": "active",
        "label": "Active",
        "count": 80,
        "students": [ { ...StudentListingDTO... } ]
      }
    ]
  }
}
```

---

## Endpoint 4: `GET /crm/students/filter`

**Breaking changes**:
1. Query parameter `has_unpaid_balance` → renamed to `has_any_outstanding_balance`
2. Response item field `enrollment_count` → renamed to `current_enrollment_count`
3. Response item field `unpaid_balance` (float) → replaced by `has_unpaid_balance` (boolean)
4. Response item adds `date_of_birth`

**Non-breaking additions**: `date_of_birth` on response items.

**Filter-specific fields preserved** on response items (not part of `StudentListingDTO` core):
- `current_group_id`, `group_default_day`, `instructor_id`, `instructor_name`
- `current_enrollment_count`, `enrolled_courses`

**Envelope**: `ApiResponse<StudentFilterResultDTO>` (unchanged)

### Query Parameters (after)

| Parameter | Type | Scope |
|---|---|---|
| `has_any_outstanding_balance` | `bool \| null` | All enrollments (active + historical) |
| *(all other parameters unchanged)* | | |

---

## Endpoint 5: `GET /crm/students/waiting-list`

**Change**: Response items gain `age` (computed) and `has_unpaid_balance` (all-enrollment scope).  
**Preserved extras**: `waiting_since`, `waiting_priority`, `waiting_notes` remain on each item.

**`has_unpaid_balance` semantics here only**: Checks ALL enrollment history, not just active enrollments. A waiting student with an unpaid balance from a prior (dropped/completed) enrollment will show `has_unpaid_balance: true`.

```json
{
  "success": true,
  "data": [
    {
      "id": 15,
      "full_name": "Sara Ali",
      "status": "waiting",
      "phone": "01098765432",
      "date_of_birth": "2014-07-20",
      "age": 11,
      "gender": "female",
      "current_group_name": null,
      "has_unpaid_balance": true,
      "waiting_since": "2026-05-01T10:00:00Z",
      "waiting_priority": 1,
      "waiting_notes": "Preferred Saturday morning"
    }
  ]
}
```

---

## Removed / Deprecated

| Symbol | Location | Action |
|---|---|---|
| `StudentListItem` | `app/api/schemas/crm/student.py` | Audit callers → delete if no other consumers remain |
| `has_unpaid_balance` query param | `GET /crm/students/filter` | Removed — renamed to `has_any_outstanding_balance` |
| `unpaid_balance` (float) response field | Filter response items | Removed — replaced by `has_unpaid_balance` boolean |
| `enrollment_count` response field | Filter response items | Renamed to `current_enrollment_count` |
