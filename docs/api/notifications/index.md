# Notification API Documentation

API documentation for the notification module, including admin settings, templates, logs, and bulk messaging.

## Base Path
All notification endpoints are prefixed with: `/api/v1/notifications`

## Routers Overview

| Router | Path | Description | Auth |
|--------|------|-------------|------|
| Admin Settings | `/admin/**` | Per-admin notification preferences and additional recipients | Admin |
| Templates | `/templates/**` | Notification template CRUD | Admin |
| Logs | `/logs/**` | Notification history and audit logs | Admin |
| Bulk | `/bulk/**` | Bulk messaging to recipients | Admin |

---

## Admin Settings API

**Base Path:** `/api/v1/notifications/admin`

### Get My Notification Settings
**GET** `/admin/settings/me`

Returns all notification settings and additional recipients for the current admin.

**Auth:** `require_admin`

**Response:** `ApiResponse<AdminSettingsResponse>`

```json
{
  "data": {
    "admin_id": 1,
    "settings": [
      {
        "notification_type": "enrollment_created",
        "is_enabled": true,
        "channel": "EMAIL",
        "description": "New enrollment confirmation"
      }
    ],
    "additional_recipients": [
      {
        "id": 1,
        "email": "manager@company.com",
        "label": "Manager",
        "notification_types": ["payment_received", "daily_report"],
        "is_active": true
      }
    ]
  }
}
```

**Notes:**
- If no settings exist for this admin, default settings are automatically created (all notifications enabled)

---

### Update My Settings (Bulk)
**PUT** `/admin/settings/me`

Bulk update notification settings for the current admin.

**Auth:** `require_admin`

**Request Body:** `UpdateAdminSettingsRequest`

```json
{
  "settings": {
    "enrollment_created": true,
    "enrollment_completed": false,
    "payment_received": true
  }
}
```

**Response:** `ApiResponse<Dict<string, boolean>>`

```json
{
  "data": {
    "enrollment_created": true,
    "enrollment_completed": false,
    "payment_received": true
  }
}
```

---

### Get Specific Notification Setting
**GET** `/admin/settings/me/types/{notification_type}`

Get a single notification type setting for the current admin.

**Auth:** `require_admin`

**Path Parameters:**
- `notification_type` (string, required): One of the 13 notification types

**Response:** `ApiResponse<AdminNotificationSettingDTO>`

**Errors:**
- `404` - Notification setting not found

---

### Toggle Specific Notification
**PUT** `/admin/settings/me/types/{notification_type}`

Enable or disable a specific notification type.

**Auth:** `require_admin`

**Path Parameters:**
- `notification_type` (string, required): One of the 13 notification types

**Request Body:** `ToggleNotificationRequest`

```json
{
  "is_enabled": false
}
```

**Response:** `ApiResponse<AdminNotificationSettingDTO>`

---

### List Additional Recipients
**GET** `/admin/settings/me/additional-recipients`

List all additional email recipients for the current admin.

**Auth:** `require_admin`

**Response:** `ApiResponse<List<AdditionalRecipientDTO>>`

```json
{
  "data": [
    {
      "id": 1,
      "email": "manager@company.com",
      "label": "Manager",
      "notification_types": ["payment_received", "daily_report"],
      "is_active": true
    }
  ]
}
```

---

### Add Additional Recipient
**POST** `/admin/settings/me/additional-recipients`

Add a new additional email recipient.

**Auth:** `require_admin`

**Request Body:** `AddRecipientRequest`

```json
{
  "email": "finance@company.com",
  "label": "Finance Team",
  "notification_types": ["monthly_report", "payment_received"]
}
```

**Notes:**
- `notification_types`: null means "all notifications"
- Each (admin_id, email) combination must be unique

**Response:** `ApiResponse<AdditionalRecipientDTO>`

**Status:** `201 Created`

---

### Update Recipient
**PUT** `/admin/settings/me/additional-recipients/{recipient_id}`

Update an existing additional recipient.

**Auth:** `require_admin`

**Path Parameters:**
- `recipient_id` (integer, required)

**Request Body:** `UpdateRecipientRequest`

```json
{
  "email": "finance@company.com",
  "label": "Finance Department",
  "notification_types": ["monthly_report"],
  "is_active": false
}
```

**Notes:**
- All fields are optional - only provided fields are updated

**Response:** `ApiResponse<AdditionalRecipientDTO>`

**Errors:**
- `404` - Recipient not found

---

### Delete Recipient
**DELETE** `/admin/settings/me/additional-recipients/{recipient_id}`

Remove an additional recipient.

**Auth:** `require_admin`

**Path Parameters:**
- `recipient_id` (integer, required)

**Response:** `ApiResponse<{ message: string }>`

**Errors:**
- `404` - Recipient not found

---

## Notification Types

| Type | Description |
|------|-------------|
| `enrollment_created` | New enrollment confirmation |
| `enrollment_completed` | Enrollment completed successfully |
| `enrollment_dropped` | Student dropped from enrollment |
| `enrollment_transferred` | Student transferred between groups |
| `level_progression` | Student progressed to next level |
| `payment_received` | Payment receipt confirmation |
| `payment_reminder` | Payment due reminder |
| `daily_report` | Daily business summary report |
| `weekly_report` | Weekly business summary report |
| `monthly_report` | Monthly business summary report |
| `competition_team_registration` | Competition team registration |
| `competition_fee_payment` | Competition fee payment receipt |
| `competition_placement` | Competition placement announcement |

---

## DTO Schemas

### AdminNotificationSettingDTO
```typescript
{
  notification_type: string;     // e.g., "enrollment_created"
  is_enabled: boolean;            // true/false
  channel: string;                // "EMAIL" (currently)
  description: string;            // Human-readable description
}
```

### AdditionalRecipientDTO
```typescript
{
  id: number;
  email: string;
  label: string | null;           // e.g., "Manager"
  notification_types: string[] | null;  // null = all notifications
  is_active: boolean;
}
```

### AdminSettingsResponse
```typescript
{
  admin_id: number;
  settings: AdminNotificationSettingDTO[];
  additional_recipients: AdditionalRecipientDTO[];
}
```

### UpdateAdminSettingsRequest
```typescript
{
  settings: Record<string, boolean>;  // notification_type -> is_enabled
}
```

### ToggleNotificationRequest
```typescript
{
  is_enabled: boolean;
}
```

### AddRecipientRequest
```typescript
{
  email: string;                    // Valid email address
  label?: string;                   // Optional label
  notification_types?: string[];      // Optional, null = all
}
```

### UpdateRecipientRequest
```typescript
{
  email?: string;
  label?: string;
  notification_types?: string[];
  is_active?: boolean;
}
```

---

## Templates API

**Base Path:** `/api/v1/notifications/templates`

See [templates.md](./templates.md) for detailed template API documentation.

---

## Logs API

**Base Path:** `/api/v1/notifications/logs`

See [logs.md](./logs.md) for detailed notification logs API documentation.

---

## Bulk Messaging API

**Base Path:** `/api/v1/notifications/bulk`

See [bulk.md](./bulk.md) for detailed bulk messaging API documentation.

---

## Common Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | UNAUTHORIZED | Missing or invalid authentication token |
| 403 | FORBIDDEN | User is not an admin |
| 404 | NOT_FOUND | Setting or recipient not found |
| 422 | VALIDATION_ERROR | Invalid request body |
| 409 | CONFLICT | Duplicate email for this admin |

---

## Usage Examples

### Disable Daily Reports
```bash
curl -X PUT /api/v1/notifications/admin/settings/me/types/daily_report \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_enabled": false}'
```

### Add Finance Team for Monthly Reports
```bash
curl -X POST /api/v1/notifications/admin/settings/me/additional-recipients \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "email": "finance@company.com",
    "label": "Finance",
    "notification_types": ["monthly_report", "payment_received"]
  }'
```

### Bulk Update Settings
```bash
curl -X PUT /api/v1/notifications/admin/settings/me \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "settings": {
      "daily_report": false,
      "weekly_report": true,
      "monthly_report": true,
      "payment_received": true,
      "enrollment_created": false
    }
  }'
```
