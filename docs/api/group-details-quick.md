# Group Details API - Quick Reference

**Base URL:** `/api/v1` | **Auth:** Bearer token (GET=any user, DELETE=admin only)

---

## 1. DELETE Level

```
DELETE /academics/groups/{group_id}/levels/{level_number}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "level_id": 45,
    "level_number": 3,
    "deleted_at": "2026-04-23T10:30:00.000Z"
  }
}
```

**Errors:** 404 (not found), 409 (has sessions/enrollments)

---

## 2. GET Levels Detailed

```
GET /academics/groups/{group_id}/levels/detailed
```

**Key Fields:**
- `courses` - Lookup table: `courses[course_id].course_name`
- `instructors` - Lookup table: `instructors[instructor_id].instructor_name`
- `levels[].sessions[]` - All sessions for the level
- `levels[].payment_summary` - Aggregated amounts
- `cache_ttl: 300` - Cache hint in seconds

**Response:**
```json
{
  "success": true,
  "data": {
    "group_id": 101,
    "cache_ttl": 300,
    "courses": { "1": { "course_id": 1, "course_name": "Robotics" } },
    "instructors": { "5": { "instructor_id": 5, "instructor_name": "Ahmed" } },
    "levels": [{
      "level_number": 1,
      "course_id": 1,
      "instructor_id": 5,
      "status": "completed",
      "sessions": [{
        "session_id": 1001,
        "date": "2026-01-15",
        "time_start": "15:00",
        "time_end": "16:30",
        "status": "completed"
      }],
      "students_count": 12,
      "payment_summary": {
        "total_expected": 36000,
        "total_collected": 35000,
        "collection_rate": 0.972
      }
    }]
  }
}
```

---

## 3. GET Attendance Grid

```
GET /academics/groups/{group_id}/attendance?level_number={n}
```

**Key Fields:**
- `roster[]` - Active students with `billing_status: "paid"|"due"`
- `sessions[].attendance` - Map: `student_id -> "present"|"absent"|null`

**Response:**
```json
{
  "success": true,
  "data": {
    "group_id": 101,
    "level_number": 1,
    "roster": [
      { "student_id": 2001, "student_name": "Omar", "billing_status": "paid" }
    ],
    "sessions": [{
      "session_id": 1001,
      "date": "2026-01-15",
      "attendance": { "2001": "present", "2002": "absent" }
    }]
  }
}
```

**Rendering:** Row=student from roster, Column=session, Cell=`session.attendance[student_id]`

---

## 4. GET Payments

```
GET /finance/groups/{group_id}/payments
```

**Key Fields:**
- `summary` - Aggregated totals across all levels
- `by_level[]` - Per-level breakdown with payments list
- `payments[].transaction_type` - `payment|refund|adjustment`

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_expected_all_levels": 72000,
      "total_collected_all_levels": 65000,
      "collection_rate": 0.903
    },
    "by_level": [{
      "level_number": 1,
      "expected": 36000,
      "collected": 35000,
      "paid_count": 11,
      "unpaid_count": 1,
      "payments": [{
        "payment_id": 8001,
        "student_name": "Omar Khaled",
        "amount": 3000,
        "payment_date": "2026-01-15",
        "status": "completed"
      }]
    }]
  }
}
```

---

## 5. GET Enrollments

```
GET /academics/groups/{group_id}/enrollments/all
```

**Key Fields:**
- `students` - Lookup table: `students[student_id].student_name`
- `grouped_by_level[].enrollments[]` - Per level, with `can_transfer`, `can_drop` flags
- `transfer_options[]` - Available groups for transfer dropdown

**Response:**
```json
{
  "success": true,
  "data": {
    "students": {
      "2001": { "student_id": 2001, "student_name": "Omar", "parent_name": "Khaled" }
    },
    "grouped_by_level": [{
      "level_number": 1,
      "enrollments": [{
        "enrollment_id": 5001,
        "student_id": 2001,
        "status": "active",
        "payment_status": "paid",
        "sessions_attended": 12,
        "can_transfer": true,
        "can_drop": true
      }],
      "summary": { "total": 12, "active": 8, "paid": 10 }
    }],
    "transfer_options": [
      { "group_id": 102, "group_name": "Advanced", "available_slots": 5 }
    ]
  }
}
```

---

## Lookup Table Pattern

Instead of repeating data, responses use lookup tables:

```typescript
// Access like this:
const courseName = response.courses[level.course_id]?.course_name;
const studentName = response.students[enrollment.student_id]?.student_name;
```

This minimizes payload size and ensures consistency.

---

## Error Format

```json
{
  "success": false,
  "error": "Human readable message"
}
```

**Status Codes:** 200 (OK), 401 (unauthorized), 403 (forbidden), 404 (not found), 409 (conflict)
