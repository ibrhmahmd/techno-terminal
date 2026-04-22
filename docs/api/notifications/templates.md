# Notification Templates API

API for managing notification templates.

**Base Path:** `/api/v1/notifications/templates`

---

## List All Templates
**GET** `/templates`

Returns all notification templates.

**Auth:** `require_admin`

**Response:** `ApiResponse<List<TemplateSummaryDTO>>`

```json
{
  "data": [
    {
      "id": 1,
      "name": "enrollment_confirmation",
      "channel": "EMAIL",
      "is_active": true,
      "is_standard": true
    }
  ]
}
```

---

## Get Template by ID
**GET** `/templates/{template_id}`

Returns full template details including body content.

**Auth:** `require_admin`

**Path Parameters:**
- `template_id` (integer, required)

**Response:** `ApiResponse<TemplateDetailDTO>`

```json
{
  "data": {
    "id": 1,
    "name": "enrollment_confirmation",
    "channel": "EMAIL",
    "subject": "Welcome! {{student_name}} enrolled",
    "body": "Dear {{parent_name}}...",
    "variables": ["parent_name", "student_name", "group_name"],
    "is_active": true,
    "is_standard": true
  }
}
```

**Errors:**
- `404` - Template not found

---

## Get Template by Name
**GET** `/templates/by-name/{template_name}`

Returns template by its unique name.

**Auth:** `require_admin`

**Path Parameters:**
- `template_name` (string, required)

**Response:** `ApiResponse<TemplateDetailDTO>`

**Errors:**
- `404` - Template not found

---

## Create Template
**POST** `/templates`

Create a new notification template.

**Auth:** `require_admin`

**Request Body:** `TemplateCreateRequest`

```json
{
  "name": "custom_template",
  "channel": "EMAIL",
  "subject": "Hello {{name}}",
  "body": "Dear {{name}}, your appointment is on {{date}}.",
  "variables": ["name", "date"],
  "is_active": true
}
```

**Notes:**
- `name` must be unique
- `channel`: "EMAIL" or "WHATSAPP" (EMAIL recommended)
- `variables`: Array of placeholder names used in subject/body
- Use `{{variable_name}}` syntax in subject and body

**Response:** `ApiResponse<TemplateDetailDTO>`

**Status:** `201 Created`

**Errors:**
- `409` - Template name already exists
- `422` - Invalid channel or missing required fields

---

## Update Template
**PUT** `/templates/{template_id}`

Update an existing template.

**Auth:** `require_admin`

**Path Parameters:**
- `template_id` (integer, required)

**Request Body:** `TemplateUpdateRequest`

```json
{
  "subject": "Updated subject {{name}}",
  "body": "Updated body content...",
  "is_active": false
}
```

**Notes:**
- Standard templates (`is_standard=true`) cannot have name/channel changed
- All fields optional - only provided fields are updated

**Response:** `ApiResponse<TemplateDetailDTO>`

**Errors:**
- `404` - Template not found
- `403` - Attempting to modify protected fields of standard template

---

## Delete Template
**DELETE** `/templates/{template_id}`

Delete a custom template. Standard templates cannot be deleted.

**Auth:** `require_admin`

**Path Parameters:**
- `template_id` (integer, required)

**Response:** `ApiResponse<{ message: string }>`

**Errors:**
- `404` - Template not found
- `403` - Cannot delete standard templates

---

## Toggle Template Status
**PUT** `/templates/{template_id}/toggle`

Quickly enable/disable a template.

**Auth:** `require_admin`

**Path Parameters:**
- `template_id` (integer, required)

**Request Body:** `TemplateToggleRequest`

```json
{
  "is_active": false
}
```

**Response:** `ApiResponse<TemplateSummaryDTO>`

---

## Test Template

**POST** `/templates/{template_id}/test`

Test a template by rendering it with placeholder values and previewing email delivery to additional recipients.

**Auth:** `require_admin`

**Path Parameters:**
- `template_id` (integer, required)

**Request Body:** None

Automatically generates placeholder values like `[Student Name]` for template variables.

**Response:** `ApiResponse<TemplateTestResultDTO>`

```json
{
  "data": {
    "template_id": 4,
    "template_name": "enrollment_confirmation",
    "rendered_subject": "[TEST] Welcome! [Student Name] enrolled",
    "rendered_body": "Dear [Parent Name], your child [Student Name]...",
    "recipients_sent": 2,
    "recipients_failed": 0,
    "errors": []
  },
  "message": "Test email would be sent to 2 recipients"
}
```

**Errors:**
- `404` - Template not found

---

## DTO Schemas

### TemplateSummaryDTO
```typescript
{
  id: number;
  name: string;
  channel: string;      // "EMAIL" | "WHATSAPP"
  is_active: boolean;
  is_standard: boolean;
}
```

### TemplateDetailDTO
```typescript
{
  id: number;
  name: string;
  channel: string;
  subject: string;
  body: string;
  variables: string[];
  is_active: boolean;
  is_standard: boolean;
}
```

### TemplateCreateRequest
```typescript
{
  name: string;         // Unique identifier
  channel: string;      // "EMAIL" recommended
  subject: string;
  body: string;
  variables: string[];
  is_active?: boolean;  // Default: true
}
```

### TemplateUpdateRequest
```typescript
{
  subject?: string;
  body?: string;
  variables?: string[];
  is_active?: boolean;
}
```

### TemplateToggleRequest
```typescript
{
  is_active: boolean;
}
```

### TemplateTestResultDTO
```typescript
{
  template_id: number;        // ID of the tested template
  template_name: string;      // Name of the template
  rendered_subject: string;   // Subject with placeholders rendered
  rendered_body: string;      // Body with placeholders rendered
  recipients_sent: number;    // Count of additional recipients
  recipients_failed: number;  // Failed send attempts
  errors: string[];          // Error messages (if any)
}
```

---

## Standard Templates

The following templates are pre-installed and cannot be deleted:

| Template | Variables |
|----------|-----------|
| `enrollment_confirmation` | parent_name, student_name, group_name, level_number, instructor_name, enrollment_id |
| `enrollment_completed` | parent_name, student_name, group_name, level_number, completion_date, enrollment_id |
| `enrollment_dropped` | parent_name, student_name, group_name, reason, enrollment_id |
| `enrollment_transferred` | parent_name, student_name, from_group_name, to_group_name, from_enrollment_id, to_enrollment_id |
| `level_progression` | parent_name, student_name, old_level, new_level, group_name, enrollment_id |
| `payment_receipt` | parent_name, student_name, amount, receipt_number, receipt_id |
| `payment_reminder` | parent_name, student_name, amount_due, due_date |
| `daily_report` | date, total_revenue, new_enrollments, sessions_held, absent_count |
| `weekly_report` | week_start, week_end, total_revenue, new_students, attendance_rate |
| `monthly_report` | month, total_revenue, new_enrollments, active_students |
| `competition_team_registration` | student_name, team_name, competition_name, category |
| `competition_fee_payment` | student_name, team_name, competition_name, amount, receipt_number |
| `competition_placement` | student_name, team_name, competition_name, placement_rank, placement_label, rank_display |

---

## Usage Examples

### Create Custom Welcome Template
```bash
curl -X POST /api/v1/notifications/templates \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "custom_welcome",
    "channel": "EMAIL",
    "subject": "Welcome {{student_name}}!",
    "body": "Hi {{parent_name}}, {{student_name}} has been enrolled in {{group_name}}.",
    "variables": ["parent_name", "student_name", "group_name"],
    "is_active": true
  }'
```

### Update Template Body
```bash
curl -X PUT /api/v1/notifications/templates/15 \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "body": "Updated message content with {{variable}}.",
    "is_active": true
  }'
```

### Disable a Template
```bash
curl -X PUT /api/v1/notifications/templates/15/toggle \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_active": false}'
```
