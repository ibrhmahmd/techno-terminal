# API Contract: Admin Notification Settings

Base path: `/api/v1/notifications/admin`
Auth: `require_admin` (Bearer JWT)

## GET /settings/me

Get all notification settings and additional recipients.

**Response** (200):
```json
{
  "success": true,
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
        "email": "admin@center.com",
        "label": "Center Director",
        "notification_types": ["enrollment_created", "payment_received"],
        "is_active": true
      }
    ]
  }
}
```

## PUT /settings/me

Bulk toggle notification settings.

**Request**:
```json
{
  "settings": {
    "enrollment_created": true,
    "payment_received": false
  }
}
```

**Response** (200): Mirrors the request settings dict.

## GET /settings/me/types/{notification_type}

Get single notification type setting. Returns 404 if not found.

## PUT /settings/me/types/{notification_type}

Toggle single notification type.

**Request**:
```json
{
  "is_enabled": true
}
```

## GET /settings/me/additional-recipients

List all additional email recipients (global).

## POST /settings/me/additional-recipients

Add recipient. Status 201.

**Request**:
```json
{
  "email": "newadmin@center.com",
  "label": "New Admin",
  "notification_types": ["enrollment_created", "payment_received"]
}
```

## PUT /settings/me/additional-recipients/{id}

Update recipient fields.

**Request** (all optional):
```json
{
  "email": "updated@center.com",
  "label": "Updated Label",
  "notification_types": ["daily_report"],
  "is_active": true
}
```

## DELETE /settings/me/additional-recipients/{id}

Remove recipient. Returns 404 if not found.
