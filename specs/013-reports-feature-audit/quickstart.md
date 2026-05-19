# Quickstart: Daily Report Fixes

## Commands

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Run specific test | `pytest tests/test_notifications.py -v` |
| Dev server | `python run_api.py` |

## Key Files

| File | Purpose |
|------|---------|
| `app/modules/notifications/services/report_notifications.py` | Main file to modify — fix attendance query, NULL fallbacks, repository delegation |
| `app/modules/notifications/repositories/reports_repository.py` | **NEW** — extract all aggregate queries here |
| `app/modules/notifications/schemas/report_dto.py` | **NEW** — `DailyReportAggregateDTO` + `PaymentDetailItem` |
| `app/modules/notifications/services/base_notification_service.py` | Fix f-string SQL interpolation in `_resolve_notification_recipients` |
| `app/api/routers/notifications/notifications_router.py` | Add `POST /reports/daily` endpoint |
| `db/migrations/056_update_daily_report_template.sql` | **NEW** — update template body with rich HTML |

## Bug Checklist

- [ ] Attendance: remove `late`/`excused` filters, use `present`/`absent`/`cancelled`
- [ ] Revenue: `COALESCE(paid_at, created_at)` in analytics query + inline payment query
- [ ] Enrollments: `COALESCE(enrolled_at, created_at)` in enrollment count query
- [ ] Repository: extract all 7 aggregate queries into `ReportsRepository`
- [ ] DTO: replace `dict` return with `DailyReportAggregateDTO`
- [ ] Dead code: delete commented-out PARENT_CODE block (lines 429-441)
- [ ] SQL injection: fix f-string in `_resolve_notification_recipients`
- [ ] Template: update daily_report body via migration to render rich HTML
- [ ] Endpoint: add `POST /api/v1/notifications/reports/daily`
