# Bulk Messaging API

API for sending bulk notifications to multiple recipients.

**Base Path:** `/api/v1/notifications/bulk`

---

## Send Bulk Notifications
**POST** `/bulk`

Send a notification to multiple recipients using a template.

**Auth:** `require_admin`

**Request Body:** `BulkNotificationRequest`

```json
{
  "template_name": "payment_reminder",
  "recipient_ids": [1, 2, 3, 4, 5],
  "recipient_type": "parent",
  "extra_variables": {
    "due_date": "2026-04-30",
    "amount_due": "500.00"
  }
}
```

**Fields:**
- `template_name` (string, required): Name of the template to use
- `recipient_ids` (integer[], required): List of recipient IDs (parent or admin IDs)
- `recipient_type` (string, required): `parent` or `admin`
- `extra_variables` (object, optional): Additional template variables

**Response:** `ApiResponse<BulkNotificationResponse>`

```json
{
  "data": {
    "total_recipients": 5,
    "queued": 5,
    "job_id": "bulk_20260421_083000"
  }
}
```

**Notes:**
- Notifications are processed asynchronously via background tasks
- Actual delivery happens after API response returns
- Check logs endpoint for delivery status

**Errors:**
- `404` - Template not found or inactive
- `400` - Invalid recipient_type or empty recipient_ids
- `422` - Missing required template variables

---

## Send to Custom Recipients
**POST** `/bulk/custom`

Send notifications to arbitrary email addresses (not system users).

**Auth:** `require_admin`

**Request Body:** `CustomBulkRequest`

```json
{
  "template_name": "announcement",
  "emails": ["user1@example.com", "user2@example.com"],
  "extra_variables": {
    "announcement_title": "New Feature",
    "announcement_body": "We have launched..."
  }
}
```

**Fields:**
- `template_name` (string, required)
- `emails` (string[], required): List of email addresses
- `extra_variables` (object, optional)

**Response:** `ApiResponse<BulkNotificationResponse>`

**Errors:**
- `400` - Invalid email format in list

---

## Get Bulk Job Status
**GET** `/bulk/jobs/{job_id}`

Check the status of a bulk notification job.

**Auth:** `require_admin`

**Path Parameters:**
- `job_id` (string, required)

**Response:** `ApiResponse<BulkJobStatusDTO>`

```json
{
  "data": {
    "job_id": "bulk_20260421_083000",
    "status": "COMPLETED",
    "total": 50,
    "sent": 48,
    "failed": 2,
    "pending": 0,
    "created_at": "2026-04-21T08:30:00Z",
    "completed_at": "2026-04-21T08:32:15Z"
  }
}
```

**Status Values:**
- `PENDING` - Job queued, not started
- `PROCESSING` - Currently sending
- `COMPLETED` - All notifications processed
- `PARTIAL` - Some failed, check logs

---

## List Recent Bulk Jobs
**GET** `/bulk/jobs`

Returns recent bulk notification jobs.

**Auth:** `require_admin`

**Query Parameters:**
- `limit` (integer, optional): Default 20, max 50
- `status` (string, optional): Filter by job status

**Response:** `ApiResponse<List<BulkJobSummaryDTO>>`

```json
{
  "data": [
    {
      "job_id": "bulk_20260421_083000",
      "template_name": "payment_reminder",
      "status": "COMPLETED",
      "total": 50,
      "sent": 48,
      "failed": 2,
      "created_at": "2026-04-21T08:30:00Z"
    }
  ]
}
```

---

## Cancel Pending Job
**DELETE** `/bulk/jobs/{job_id}`

Cancel a pending bulk job (only works if not yet started).

**Auth:** `require_admin`

**Path Parameters:**
- `job_id` (string, required)

**Response:** `ApiResponse<{ cancelled: boolean }>`

**Errors:**
- `404` - Job not found
- `409` - Cannot cancel - job already processing or completed

---

## DTO Schemas

### BulkNotificationRequest
```typescript
{
  template_name: string;
  recipient_ids: number[];
  recipient_type: "parent" | "admin";
  extra_variables?: Record<string, any>;
}
```

### CustomBulkRequest
```typescript
{
  template_name: string;
  emails: string[];
  extra_variables?: Record<string, any>;
}
```

### BulkNotificationResponse
```typescript
{
  total_recipients: number;
  queued: number;
  job_id: string;
}
```

### BulkJobStatusDTO
```typescript
{
  job_id: string;
  status: string;           // "PENDING" | "PROCESSING" | "COMPLETED" | "PARTIAL"
  total: number;
  sent: number;
  failed: number;
  pending: number;
  created_at: string;
  completed_at?: string;
}
```

### BulkJobSummaryDTO
```typescript
{
  job_id: string;
  template_name: string;
  status: string;
  total: number;
  sent: number;
  failed: number;
  created_at: string;
}
```

---

## Usage Examples

### Send Payment Reminders to All Active Students
```bash
curl -X POST /api/v1/notifications/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "payment_reminder",
    "recipient_ids": [101, 102, 103, 104, 105],
    "recipient_type": "parent",
    "extra_variables": {
      "due_date": "2026-05-01",
      "amount_due": "450.00"
    }
  }'
```

### Send Announcement to Admins
```bash
curl -X POST /api/v1/notifications/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "announcement",
    "recipient_ids": [1, 2, 3],
    "recipient_type": "admin",
    "extra_variables": {
      "title": "System Maintenance",
      "message": "Maintenance scheduled for tonight."
    }
  }'
```

### Send to External Email List
```bash
curl -X POST /api/v1/notifications/bulk/custom \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "newsletter",
    "emails": ["contact1@partner.com", "contact2@partner.com"],
    "extra_variables": {
      "month": "April 2026",
      "highlights": "New competition season starting!"
    }
  }'
```

### Check Job Status
```bash
curl "/api/v1/notifications/bulk/jobs/bulk_20260421_083000" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rate Limits

| Operation | Limit |
|-----------|-------|
| Bulk send | 1,000 recipients per request |
| Custom bulk | 500 emails per request |
| Job status checks | No limit |

---

## Best Practices

1. **Batch Large Sends**: Split >1000 recipients into multiple requests
2. **Check Status**: Poll job status endpoint for large batches
3. **Monitor Logs**: Failed individual notifications appear in logs
4. **Use Templates**: Always use pre-created templates for consistency
5. **Test First**: Send to small test group before bulk sending
