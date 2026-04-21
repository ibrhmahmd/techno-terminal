# Notification Logs API

API for querying notification history and audit logs.

**Base Path:** `/api/v1/notifications/logs`

---

## List Notification Logs
**GET** `/logs`

Returns paginated notification logs with filtering options.

**Auth:** `require_admin`

**Query Parameters:**
- `status` (string, optional): Filter by status - `PENDING`, `SENT`, `FAILED`
- `channel` (string, optional): Filter by channel - `EMAIL`, `WHATSAPP`
- `recipient_type` (string, optional): `PARENT`, `ADMIN`, `EMPLOYEE`, `ADDITIONAL`
- `template_id` (integer, optional): Filter by template
- `from_date` (string, optional): ISO date format (2026-01-01)
- `to_date` (string, optional): ISO date format (2026-01-31)
- `page` (integer, optional): Page number, default 1
- `limit` (integer, optional): Items per page, default 20, max 100

**Response:** `ApiResponse<PaginatedNotificationLogResponse>`

```json
{
  "data": {
    "items": [
      {
        "id": 1,
        "template_id": 1,
        "template_name": "enrollment_confirmation",
        "channel": "EMAIL",
        "recipient_type": "ADMIN",
        "recipient_id": 5,
        "recipient_contact": "admin@company.com",
        "status": "SENT",
        "subject": "Welcome! John Doe enrolled",
        "created_at": "2026-04-21T08:30:00Z",
        "sent_at": "2026-04-21T08:30:02Z",
        "error_message": null
      }
    ],
    "total": 150,
    "page": 1,
    "limit": 20,
    "pages": 8
  }
}
```

---

## Get Log by ID
**GET** `/logs/{log_id}`

Returns detailed information about a specific notification log.

**Auth:** `require_admin`

**Path Parameters:**
- `log_id` (integer, required)

**Response:** `ApiResponse<NotificationLogDetailDTO>`

```json
{
  "data": {
    "id": 1,
    "template_id": 1,
    "template_name": "enrollment_confirmation",
    "channel": "EMAIL",
    "recipient_type": "ADMIN",
    "recipient_id": 5,
    "recipient_contact": "admin@company.com",
    "status": "SENT",
    "subject": "Welcome! John Doe enrolled",
    "body": "Full rendered body content...",
    "variables_used": {
      "parent_name": "Admin",
      "student_name": "John Doe",
      "group_name": "Level 1 - Group A"
    },
    "created_at": "2026-04-21T08:30:00Z",
    "sent_at": "2026-04-21T08:30:02Z",
    "error_message": null
  }
}
```

**Errors:**
- `404` - Log entry not found

---

## Get Failed Notifications
**GET** `/logs/failed`

Returns failed notifications for troubleshooting.

**Auth:** `require_admin`

**Query Parameters:**
- `from_date` (string, optional): ISO date format
- `to_date` (string, optional): ISO date format
- `limit` (integer, optional): Max 100, default 50

**Response:** `ApiResponse<List<NotificationLogDTO>>`

---

## Get Statistics
**GET** `/logs/statistics`

Returns aggregated statistics for notifications.

**Auth:** `require_admin`

**Query Parameters:**
- `from_date` (string, required): ISO date format
- `to_date` (string, required): ISO date format
- `group_by` (string, optional): `day`, `template`, `channel`, `status`

**Response:** `ApiResponse<NotificationStatisticsDTO>`

```json
{
  "data": {
    "total": 1000,
    "by_status": {
      "SENT": 950,
      "FAILED": 45,
      "PENDING": 5
    },
    "by_channel": {
      "EMAIL": 1000
    },
    "by_template": {
      "enrollment_confirmation": 150,
      "payment_receipt": 200
    }
  }
}
```

---

## Retry Failed Notification
**POST** `/logs/{log_id}/retry`

Manually retry a failed notification.

**Auth:** `require_admin`

**Path Parameters:**
- `log_id` (integer, required)

**Response:** `ApiResponse<{ success: boolean, new_log_id: number }>`

**Notes:**
- Creates a new log entry for the retry attempt
- Original failed log remains in history

**Errors:**
- `404` - Log entry not found
- `400` - Cannot retry non-failed notification

---

## DTO Schemas

### NotificationLogDTO
```typescript
{
  id: number;
  template_id: number;
  template_name: string;
  channel: string;
  recipient_type: string;
  recipient_id: number;
  recipient_contact: string;
  status: string;           // "PENDING" | "SENT" | "FAILED"
  subject: string;
  created_at: string;       // ISO 8601
  sent_at: string | null;
  error_message: string | null;
}
```

### NotificationLogDetailDTO
```typescript
{
  id: number;
  template_id: number;
  template_name: string;
  channel: string;
  recipient_type: string;
  recipient_id: number;
  recipient_contact: string;
  status: string;
  subject: string;
  body: string;              // Full rendered content
  variables_used: Record<string, any>;
  created_at: string;
  sent_at: string | null;
  error_message: string | null;
}
```

### PaginatedNotificationLogResponse
```typescript
{
  items: NotificationLogDTO[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
```

### NotificationStatisticsDTO
```typescript
{
  total: number;
  by_status: Record<string, number>;
  by_channel: Record<string, number>;
  by_template: Record<string, number>;
  by_day?: Record<string, number>;
}
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Notification queued but not yet sent |
| `SENT` | Successfully dispatched |
| `FAILED` | Failed to send (see error_message) |

---

## Recipient Types

| Type | Description |
|------|-------------|
| `ADMIN` | System admin user |
| `ADDITIONAL` | Additional recipient configured by admin |
| `PARENT` | Student parent (currently disabled) |
| `EMPLOYEE` | Staff member (legacy) |

---

## Usage Examples

### Query Recent Failed Emails
```bash
curl "/api/v1/notifications/logs?status=FAILED&channel=EMAIL&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Statistics for Last 7 Days
```bash
curl "/api/v1/notifications/logs/statistics?from_date=2026-04-14&to_date=2026-04-21&group_by=day" \
  -H "Authorization: Bearer $TOKEN"
```

### Retry a Failed Notification
```bash
curl -X POST /api/v1/notifications/logs/123/retry \
  -H "Authorization: Bearer $TOKEN"
```
