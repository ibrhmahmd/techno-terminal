# Tasks: Date-Parameterized Daily Report Endpoints

## Phase 1: Schema & Service Methods

- [ ] T001 Add `DailyReportRequest` Pydantic schema in `app/api/schemas/notifications/report_request.py` — body with optional `email_recipients: list[str]`
- [ ] T002 Add `_has_data(aggregates)` to `ReportNotificationService` — returns False if sessions_held=0, payment_count=0, new_enrollments=0
- [ ] T003 Add `get_daily_report_pdf_base64(target_date)` to `ReportNotificationService` — returns base64-encoded PDF bytes
- [ ] T004 Add `send_daily_report_to_recipients(target_date, recipients)` to `ReportNotificationService` — sends to specific list, returns count
- [ ] T005 Add `get_daily_report_data(target_date)` to `ReportNotificationService` — returns `DailyReportAggregateDTO`

## Phase 2: Endpoints

- [ ] T006 Modify `POST /reports/daily` — accept `target_date` query param + `DailyReportRequest` body, two modes
- [ ] T007 Add `GET /reports/daily/data` — returns `DailyReportAggregateDTO` JSON

## Phase 3: Polish

- [ ] T008 Return 404 for dates with no data in both endpoints
- [ ] T009 Validate email format in `email_recipients` list
- [ ] T010 Test both endpoints
