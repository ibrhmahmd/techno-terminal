# Daily Reports API

Base path: `/api/v1/notifications/reports/daily`

All endpoints require `Authorization: Bearer <jwt>` header with `admin` or `system_admin` role.

---

## POST `/api/v1/notifications/reports/daily`

Trigger daily report. Two modes depending on request body:

### Mode A — Get PDF (base64)

Send with **no body**. Returns a base64-encoded PDF attachment.

```
POST /api/v1/notifications/reports/daily?target_date=2026-05-20
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "date": "2026-05-20",
    "pdf_base64": "JVBERi0xLjQKMSAwIG9iago8..."
  },
  "message": null
}
```

### Mode B — Email to recipients

Send with a JSON body listing recipient emails.

```
POST /api/v1/notifications/reports/daily?target_date=2026-05-20
Content-Type: application/json

{
  "email_recipients": ["admin@example.com", "manager@example.com"]
}
```

**Response** (200):
```json
{
  "success": true,
  "data": "Daily report queued for 2 recipient(s)",
  "message": null
}
```

### Errors

| Status | Condition |
|--------|-----------|
| 404 | No data for the requested date (sessions=0 AND payments=0 AND enrollments=0) |
| 422 | Invalid email format in `email_recipients` |
| 401 | Missing/invalid auth |

---

## GET `/api/v1/notifications/reports/daily/data`

Get the report data as JSON (no email or PDF).

```
GET /api/v1/notifications/reports/daily/data?target_date=2026-05-20
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "date": "2026-05-20",
    "total_revenue": 0.0,
    "new_enrollments": 4,
    "sessions_held": 1,
    "present_count": 4,
    "absent_count": 3,
    "attendance_rate": 0.571,
    "payment_count": 0,
    "payment_methods": {},
    "payment_details": [],
    "instructors_list": ["ibrahim el-marya"],
    "session_details": [
      {
        "instructor_name": "ibrahim el-marya",
        "session_time": "18:00 - 20:00",
        "present_count": 4,
        "absent_count": 3,
        "cancelled_count": 0,
        "student_names_present": "asiaa amr shereif, ibrahim ahmed abo elenin, karma mahmoud mahdy, Karma mahmoud mahdy Kandeel",
        "student_names_absent": "Aseyah amr sherif, Sereen Ahmad AlGanzory, Sila Ahmad AlGanzory"
      }
    ],
    "payments_by_type": [],
    "instructor_summary": [
      {
        "instructor_name": "ibrahim el-marya",
        "session_count": 1
      }
    ]
  },
  "message": null
}
```

---

## Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `target_date` | `date` (ISO: `YYYY-MM-DD`) | today | The report date |

---

## Data Structure

| Field | Type | Description |
|-------|------|-------------|
| `total_revenue` | float | Net revenue (payments - refunds) |
| `new_enrollments` | int | Enrollments created on this date |
| `sessions_held` | int | Completed sessions |
| `present_count` | int | Attendance marked present |
| `absent_count` | int | Attendance marked absent |
| `attendance_rate` | float | present / (present + absent) |
| `payment_count` | int | Number of payments |
| `payment_methods` | object | `{"cash": 3, "card": 2}` |
| `payment_details` | array | Per-payment breakdown |
| `instructors_list` | array | Unique instructor names |
| `session_details` | array | Per-session attendance breakdown |
| `payments_by_type` | array | Payments grouped by type, with subtotals |
| `instructor_summary` | array | Instructor name + session count |

### payment_details item

| Field | Type |
|-------|------|
| `student_name` | string |
| `group_name` | string |
| `amount` | float |
| `payment_type` | string |

### session_details item

| Field | Type |
|-------|------|
| `instructor_name` | string |
| `session_time` | string (e.g. `"18:00 - 20:00"`) |
| `present_count` | int |
| `absent_count` | int |
| `cancelled_count` | int |
| `student_names_present` | string (comma-separated) |
| `student_names_absent` | string (comma-separated) |

### payments_by_type item

| Field | Type | Description |
|-------|------|-------------|
| `payment_type` | string | e.g. `"cash"`, `"card"`, `"course_level"` |
| `subtotal` | float | Sum of amounts in this type |
| `count` | int | Number of payments |
| `items` | array | `payment_details[]` for this type |

### instructor_summary item

| Field | Type |
|-------|------|
| `instructor_name` | string |
| `session_count` | int |

---

## Common Errors

```json
{
  "success": false,
  "error": "NotFoundError",
  "message": "No data found for 2026-05-21"
}
```

```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Could not validate credentials with Supabase"
}
```
