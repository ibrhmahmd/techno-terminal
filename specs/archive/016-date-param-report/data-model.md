# Data Model: Date-Parameterized Daily Report

## New Schemas

### DailyReportRequest (app/api/schemas/notifications/report_request.py)
```python
class DailyReportRequest(BaseModel):
    email_recipients: Optional[list[str]] = None  # validated via regex
```

## New Service Methods (ReportNotificationService)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `get_daily_report_pdf_base64` | `target_date: date` | `tuple[str, str]` | Returns (date_str, base64_pdf) |
| `get_report_assets` | `target_date: date` | `tuple[attachments, variables, template]` | Builds PDF + vars for dispatch |
| `get_daily_report_data` | `target_date: date` | `DailyReportAggregateDTO` | Returns aggregate data |
| `_has_data` | `aggregates: DTO` | `bool` | True if any metric > 0 |
| `_build_variables` | `aggregates, date` | `dict` | Template variable dict |
| `_build_daily_report_body` | `aggregates, date` | `str` | Rendered HTML body |

## No New Models or Migrations
All data comes from existing `DailyReportAggregateDTO` and `ReportsRepository`.
