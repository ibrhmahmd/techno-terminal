# API Contracts: Fix Daily Report Critical Bugs

## Changed Contracts

### POST /api/v1/notifications/reports/daily
### GET /api/v1/notifications/reports/data?date={date}

**Change**: Both now return **400 Bad Request** when `report_date > date.today()`.

```json
{
  "success": false,
  "error": "Bad Request",
  "message": "Report date cannot be in the future"
}
```

## Unchanged Contracts

- `DailyReportAggregateDTO` — already typed, no changes
- `PaymentDetailItem` — already typed, no changes
- `DailyReportRequest` — already typed, no changes
- Notification log creation — unchanged
- Email dispatch — unchanged

See `docs/api/daily-reports.md` for full endpoint reference.
