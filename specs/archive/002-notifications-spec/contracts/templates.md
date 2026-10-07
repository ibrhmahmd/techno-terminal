# API Contract: Notification Templates

Base path: `/api/v1/notifications`
Auth: `require_admin` (Bearer JWT)

## GET /templates

List all notification templates.

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "enrollment_confirmation",
      "subject": "New Enrollment: {{student_name}}",
      "body": "Student {{student_name}} has been enrolled in group {{group_name}}.",
      "variables": ["student_name", "group_name", "level"],
      "is_standard": true,
      "is_active": true
    }
  ]
}
```

## GET /templates/{id}

Get single template. Returns 404 if not found.

## POST /templates

Create a new template.

**Request**:
```json
{
  "name": "custom_alert",
  "subject": "Alert: {{message}}",
  "body": "{{message}}",
  "variables": ["message"]
}
```

**Response** (201): TemplateDTO with id assigned.

**Constraints**: `name` unique; `variables` optional array.

## PUT /templates/{id}

Update template. Blocked on standard templates for `name`, `variables` fields. Returns 404 if not found.

## DELETE /templates/{id}

Delete template. Blocked if `is_standard == true`. Returns 404 if not found.

## POST /templates/{id}/test

Test-send a rendered template to all active additional recipients.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "template_id": 1,
    "template_name": "enrollment_confirmation",
    "rendered_subject": "[TEST] New Enrollment: [Student Name]",
    "rendered_body": "Student [Student Name] has been enrolled in group [Group Name].",
    "recipients_sent": 3,
    "recipients_failed": 0,
    "errors": []
  }
}
```
