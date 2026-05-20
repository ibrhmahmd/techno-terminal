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

## Phase 1 Checklist (Bug Fixes — DONE)

- [x] Attendance: remove `late`/`excused` filters, use `present`/`absent`/`cancelled`
- [x] Revenue: `COALESCE(paid_at, created_at)` in analytics query + inline payment query
- [x] Enrollments: `COALESCE(enrolled_at, created_at)` in enrollment count query
- [x] Repository: extract all 7 aggregate queries into `ReportsRepository`
- [x] DTO: replace `dict` return with `DailyReportAggregateDTO`
- [x] Dead code: delete commented-out PARENT_CODE block (lines 429-441)
- [x] SQL injection: fix f-string in `_resolve_notification_recipients`
- [x] Endpoint: add `POST /api/v1/notifications/reports/daily`

## Phase 2 Checklist (Rich Tables — NOT STARTED)

- [ ] DTO: add `SessionDetailItem`, `PaymentTypeGroup`, `InstructorSummaryItem` to `report_dto.py`
- [ ] Repository: add `_fetch_session_details()` and `_fetch_instructor_summary()` to `ReportsRepository`
- [ ] Repository: group payments by type in `_fetch_payments()`
- [ ] Service: build per-session attendance HTML table in `send_daily_report()`
- [ ] Service: build payment type sub-tables with subtotals in `send_daily_report()`
- [ ] Service: build instructor summary HTML table in `send_daily_report()`
- [ ] PDF: add per-session attendance table section in `daily_report_pdf.py`
- [ ] PDF: add payments-by-type sub-tables section in `daily_report_pdf.py`
- [ ] PDF: add instructor summary table section in `daily_report_pdf.py`
- [ ] Template: update `daily_report` body via migration to include 3 new table variables
