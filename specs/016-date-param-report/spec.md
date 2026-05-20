# Spec: Date-Parameterized Daily Report Endpoints

## User Story
As an admin, I want to generate daily reports for any chosen date, either downloading the PDF or sending it to specific email recipients, so I can review historical data or share reports with stakeholders.

## Requirements

### REQ-1: Modify POST /reports/daily to accept target_date
- Add optional `target_date` query parameter (ISO format `YYYY-MM-DD`)
- Defaults to today if omitted
- Returns 404 if no data exists for that date

### REQ-2: Two output modes
- **Mode A (no email_recipients)**: Returns `{"success": true, "data": {"pdf_base64": "..."}}`
- **Mode B (with email_recipients)**: Sends PDF + HTML report to each recipient, returns `{"success": true, "data": "Report sent to N recipient(s)"}`

### REQ-3: Email recipients in request body
```json
{"email_recipients": ["admin@example.com", "manager@example.com"]}
```

### REQ-4: GET /reports/daily/data
- Returns `DailyReportAggregateDTO` as JSON
- Optional `target_date` query param (defaults to today)
- Returns 404 if no data exists

### REQ-5: 404 behavior
A date has "no data" if ALL of these are zero/empty: sessions_held=0, payment_count=0, new_enrollments=0

## Edge Cases
- Date in the future: returns 404 (no data)
- Invalid date format: returns 422 validation error
- Non-existent date (e.g. Feb 30): returns 422
- Date with only attendance but no payments: returns report with zeros for payment fields
- Empty email_recipients list: treated as Mode A (return PDF)
- Invalid email in recipients: returns 422 with specific email validation error
