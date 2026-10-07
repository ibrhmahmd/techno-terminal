# API Contract: Notification Events

Base path: `/api/v1/notifications`
Auth: `require_admin` (Bearer JWT)

## POST /absence

Trigger an absence alert notification.

**Request**:
```json
{
  "student_id": 123,
  "session_name": "Math Level 3 - Session 5",
  "session_date": "2026-05-12"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": null,
  "message": "Absence alert sent"
}
```

**Behavior**: Resolves student parent contact, looks up `absence_alert` template, dispatches to all active recipients subscribed to enrollment notifications.

---

## POST /receipt/{receipt_id}

Trigger a payment receipt notification.

**Query params**: `student_id`, `amount`, `receipt_number`

**Response** (200):
```json
{
  "success": true,
  "data": null,
  "message": "Receipt notification sent"
}
```

**Behavior**: Generates PDF receipt attachment, sends email with attachment to all active recipients subscribed to payment notifications.

---

## GET /logs

List notification logs (paginated).

**Query params**: `limit` (default 50), `offset` (default 0)

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "template_id": 3,
      "channel": "EMAIL",
      "recipient_type": "ADDITIONAL",
      "recipient_id": 5,
      "recipient_contact": "admin@center.com",
      "subject": "Enrollment Confirmed",
      "body": "Student John has been enrolled...",
      "status": "SENT",
      "error_message": null,
      "retry_count": 0,
      "next_retry_at": null,
      "sent_at": "2026-05-12T10:00:00Z",
      "created_at": "2026-05-12T10:00:00Z"
    }
  ]
}
```

---

## POST /logs/{log_id}/retry

Manually retry a failed notification.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "log_id": 42,
    "status": "PENDING",
    "message": "Retry queued"
  }
}
```

**Error** (404): Log not found
**Error** (409): Log status is not FAILED
