# Quickstart: Daily Report Redesign & Debtors Data

## Files to Modify

| File | What to Change |
|------|---------------|
| `app/modules/notifications/schemas/report_dto.py` | Add new DTOs: `UnpaidAttendeeItem`, `TopDebtorItem`, `OutstandingByGroupItem`, `TomorrowPreviewDTO`. Extend `DailyReportAggregateDTO` with 6 new fields |
| `app/modules/notifications/repositories/reports_repository.py` | Add `_fetch_tomorrow_preview()` method. Add debtors data queries (or call through module root) |
| `app/modules/notifications/services/report_notifications.py` | Update `send_daily_report()` to fetch debtors data. Update `_build_variables()` to render new HTML sections. Update `_fetch_daily_aggregates()` to call debtors queries. Update `get_daily_report_data()` etc. |
| `scripts/test_report_email.py` | New file — CLI script for test email with hardcoded date 2026-05-24 |
| `db/migrations/058_update_daily_report_precision_engine.sql` | New migration — update `daily_report` template body with Precision Engine HTML |

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/test_report_email.py` | CLI script: generates report for 2026-05-24, sends to specified email |
| `db/migrations/058_update_daily_report_precision_engine.sql` | Template body update |

## Execution Order

1. Add new DTOs to `report_dto.py`
2. Extend `DailyReportAggregateDTO` with new fields
3. Add `_fetch_tomorrow_preview()` to `ReportsRepository`
4. Update `ReportNotificationService._fetch_daily_aggregates()` to call debtors + tomorrow queries
5. Update `ReportNotificationService._build_variables()` to render new HTML sections
6. Update public methods (`send_daily_report`, `get_daily_report_data`, etc.)
7. Create `scripts/test_report_email.py`
8. Create migration `058_update_daily_report_precision_engine.sql`

## Test Email Command

```powershell
python scripts/test_report_email.py --to admin@example.com
```

## Verification

```powershell
pytest tests/test_notifications.py -v
```
