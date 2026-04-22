# Template Testing API

API for testing notification templates by rendering with placeholder values and previewing email delivery.

**Base Path:** `/api/v1/notifications/templates`

---

## Test Template

**POST** `/templates/{template_id}/test`

Renders a template with placeholder values and returns a preview of the rendered content along with the count of recipients who would receive the test email.

**Auth:** `require_admin`

**Path Parameters:**
- `template_id` (integer, required) - ID of the template to test

**Request Body:** None

The endpoint automatically generates placeholder values for all template variables (e.g., `{{student_name}}` becomes `[Student Name]`).

**Response:** `ApiResponse<TemplateTestResultDTO>`

```json
{
  "data": {
    "template_id": 4,
    "template_name": "enrollment_confirmation",
    "rendered_subject": "[TEST] Welcome! [Student Name] enrolled",
    "rendered_body": "Dear [Parent Name], your child [Student Name] has been enrolled in [Group Name]. Instructor: [Instructor Name].",
    "recipients_sent": 2,
    "recipients_failed": 0,
    "errors": []
  },
  "message": "Test email would be sent to 2 recipients"
}
```

**Errors:**
- `404` - Template not found
- `401` - Unauthorized (admin only)

---

## DTO Schemas

### TemplateTestResultDTO

```typescript
{
  template_id: number;        // ID of the tested template
  template_name: string;      // Name of the template
  rendered_subject: string;   // Subject line with placeholders rendered
  rendered_body: string;      // Body content with placeholders rendered
  recipients_sent: number;    // Count of additional recipients who would receive the email
  recipients_failed: number;  // Count of failed send attempts (currently always 0)
  errors: string[];          // Array of error messages (if any)
}
```

---

## Placeholder Generation

When testing a template, the system automatically generates human-readable placeholder values:

| Template Variable | Rendered Value |
|-------------------|----------------|
| `{{parent_name}}` | `[Parent Name]` |
| `{{student_name}}` | `[Student Name]` |
| `{{group_name}}` | `[Group Name]` |
| `{{instructor_name}}` | `[Instructor Name]` |
| `{{enrollment_id}}` | `[Enrollment Id]` |
| `{{amount}}` | `[Amount]` |

The pattern converts snake_case to Title Case and wraps in brackets.

---

## Usage Examples

### Test Enrollment Confirmation Template

```bash
curl -X POST http://localhost:8000/api/v1/notifications/templates/1/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "data": {
    "template_id": 1,
    "template_name": "enrollment_confirmation",
    "rendered_subject": "[TEST] Welcome! [Student Name] enrolled",
    "rendered_body": "Dear [Parent Name], your child [Student Name] has been enrolled in [Group Name] (Level [Level Number]). Instructor: [Instructor Name].",
    "recipients_sent": 3,
    "recipients_failed": 0,
    "errors": []
  },
  "message": "Test email would be sent to 3 recipients"
}
```

### Test Payment Receipt Template

```bash
curl -X POST http://localhost:8000/api/v1/notifications/templates/6/test \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "data": {
    "template_id": 6,
    "template_name": "payment_receipt",
    "rendered_subject": "[TEST] Payment Received - Receipt #[Receipt Number]",
    "rendered_body": "Dear [Parent Name], we received payment of [Amount] for [Student Name]. Receipt Number: [Receipt Number].",
    "recipients_sent": 3,
    "recipients_failed": 0,
    "errors": []
  },
  "message": "Test email would be sent to 3 recipients"
}
```

---

## How It Works

1. **Template Loading**: The endpoint loads the specified template by ID
2. **Placeholder Generation**: For each variable in `template.variables`, generates a human-readable placeholder
3. **Rendering**: Substitutes all `{{variable}}` placeholders with generated values
4. **Subject Prefix**: Adds `[TEST]` prefix to the subject line to identify test emails
5. **Recipient Count**: Queries the `notification_additional_recipients` table for all active recipients
6. **Result Return**: Returns the rendered content and recipient count (emails are not actually sent in current implementation)

---

## Related Endpoints

- [Templates API](./templates.md) - Manage notification templates
- [Admin Settings API](./admin_settings.md) - Configure additional recipients
