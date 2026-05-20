# Plan: Date-Parameterized Daily Report Endpoints

## Architecture
- Modify existing `POST /api/v1/notifications/reports/daily` to accept optional `target_date` + body
- Add `GET /api/v1/notifications/reports/daily/data`
- Use existing `ReportsRepository` and `ReportNotificationService`
- No new models or migrations

## Flow

### POST Mode A (return PDF base64)
```
POST /reports/daily?target_date=2026-05-15
  → trigger_daily_report(target_date, email_recipients=None)
    → svc.report.get_daily_report_pdf_base64(target_date)
      → _fetch_daily_aggregates(target_date)
      → check has_data() else 404
      → generate_daily_report_pdf(...)
      → base64 encode
    ← {"pdf_base64": "..."}
```

### POST Mode B (send email)
```
POST /reports/daily?target_date=2026-05-15
  Body: {"email_recipients": ["a@x.com"]}
  → trigger_daily_report(target_date, email_recipients=["a@x.com"])
    → svc.report.send_daily_report_to_recipients(target_date, recipients)
      → _fetch_daily_aggregates(target_date)
      → check has_data() else 404
      → generate PDF
      → send email to each recipient
    ← "Report sent to 1 recipient(s)"
```

### GET /reports/daily/data
```
GET /reports/daily/data?target_date=2026-05-15
  → get_daily_report_data(target_date)
    → _fetch_daily_aggregates(target_date)
    → check has_data() else 404
    ← DailyReportAggregateDTO JSON
```

## Implementation Order
1. Add schema for request body (`DailyReportRequest`)
2. Add helper methods to `ReportNotificationService`:
   - `get_daily_report_pdf_base64(date) → str`
   - `send_daily_report_to_recipients(date, recipients) → int`
   - `get_daily_report_data(date) → DailyReportAggregateDTO`
   - `_has_data(aggregates) → bool`
3. Modify POST endpoint
4. Add GET endpoint
5. Test
