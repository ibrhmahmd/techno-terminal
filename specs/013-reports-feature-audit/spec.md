# Feature Specification: Reports Feature Audit

**Feature Branch**: `013-reports-feature-audit`
**Created**: 2026-05-19
**Status**: Clarified (daily report scope)
**Input**: Full audit of daily/weekly/monthly report features — services logic, DB queries, template bodies, insights, PDF styling, scheduler timing, and business alignment.

## Clarifications

### Session 2026-05-19

- Q: How should the attendance status bug (query filters for non-existent `late`/`excused` values) be resolved? → A: Remove `late`/`excused` from query. Count only `present`, `absent`, `cancelled` as defined in domain constant and DB CHECK constraint. No schema migration needed.
- Q: How to handle `receipts.paid_at` being NULL, causing revenue/payment queries to return 0? → A: Fallback to `created_at` in daily report queries using `COALESCE(paid_at, created_at)`. Do not modify the receipt creation flow.
- Q: Should the unused daily report variables be removed from computation or should the email template be updated to render them? → A: Update the email template to render the rich metrics (payment details table, attendance rate, instructor list, payment methods breakdown, unpaid count). The data is already fetched; make the email as useful as the PDF.
- Q: Should the raw SQL queries inside `_fetch_daily_aggregates()` be refactored to use the analytics repository as the single source of truth? → A: Yes. Move all aggregate queries out of the service into the analytics `financial_repository.py` or a dedicated reports repository. The service should call typed repository methods, not execute raw SQL.
- Q: Should `enrollments.enrolled_at` NULL values also get a COALESCE fallback (like `paid_at`)? → A: Yes. Use `COALESCE(enrolled_at, created_at)` for enrollment queries AND `COALESCE(paid_at, created_at)` for receipts. Consistent fallback across all date-based report queries.

---

## Executive Summary

The reports feature (`ReportNotificationService` + `ReportScheduler` + `daily_report_pdf.py`) is functionally working but has 15+ issues across 6 dimensions. The daily report is the most mature (PDF attachment, rich metrics, HTML payment table). Weekly and monthly reports are thin — 3 metrics each, no PDF, no actionable insights beyond raw numbers. The scheduler relies on in-memory state lost on restart. Several queries use attendance status values (`late`, `excused`) that don't exist in the domain model. Template variables are computed but never rendered in email bodies.

---

## User Scenarios & Testing

### User Story 1 — Daily report has accurate attendance metrics (P1)

The attendance breakdown in the daily report shows absent, present (including late), and excused counts. The attendance rate is used in the PDF summary card.

**Bug Found**: `_fetch_daily_aggregates()` queries for `Attendance.status IN ('present', 'late')` and `Attendance.status == 'excused'`, but the domain model defines `AttendanceStatus = Literal['present', 'absent', 'cancelled']`. The `late` and `excused` statuses **do not exist** in the database. The present+late count always equals present count, and excused is always 0.

**Acceptance**:
1. **Given** an attendance record marked with status `present`, **When** `_fetch_daily_aggregates` runs, **Then** it counts as `present_count`.
2. **Given** the domain only has `present`, `absent`, `cancelled` statuses, **When** the attendance query filters for `late` or `excused`, **Then** those counts are always zero (bug).
3. **Fix**: Remove `late` and `excused` references from the query. Count only `present`, `absent`, `cancelled`. No DB migration needed.

### User Story 2 — Monthly report covers the preceding full month (P1)

The monthly report fires on day 1 of each month. It should report on the **full preceding calendar month** (e.g., on April 1, report on March 1–31).

**Bug Found**: `_fetch_monthly_aggregates(month_start, today)` where `month_start = today.replace(day=1)` and `today = date.today()`. On April 1, `month_start` = April 1, so the report covers April 1 only — **one day**, not the full preceding month.

**Acceptance**:
1. **Given** today is April 1, **When** `_fetch_monthly_aggregates` is called, **Then** the date range should be March 1–March 31 (or March 1–today), not April 1–April 1.
2. **Given** the report is sent on day 1, **When** the revenue is calculated, **Then** it reflects the full previous calendar month, not the current month-to-date.

### User Story 3 — Weekly report covers the full preceding 7 days (P2)

The weekly report fires on Monday. It should cover the previous Monday–Sunday (7 days).

**Bug Found**: `week_start = today - timedelta(days=today.weekday())` where `today.weekday() == 0` on Monday gives `week_start = today`. So on Monday, the report covers **just today** (1 day), not the preceding 7 days. To cover the previous week: `week_start = today - timedelta(days=7)`.

**Acceptance**:
1. **Given** today is Monday (day 0), **When** `_fetch_weekly_aggregates` is called, **Then** `week_start` should be 7 days before today.
2. **Given** the report fires on Monday, **When** revenue is calculated, **Then** it reflects Monday–Sunday of the preceding week.

### User Story 4 — Weekly report "attendance rate" metric is correctly named (P2)

**Bug Found**: The weekly report shows an "Attendance Rate" metric, but the computation is `active_count / total_enrollments` from `BIAnalyticsService.get_retention_metrics()`. This is a **retention/active rate**, not an attendance rate. The template labels it misleadingly.

**Acceptance**:
1. **Given** the weekly report template has `{{attendance_rate}}`, **When** the report is generated, **Then** the value should represent actual session attendance (not enrollment retention), OR the label should change to "Active Enrollment Rate".

### User Story 5 — Template variables match what the email body renders (P2)

**Bug Found**: `send_daily_report()` passes 11 variables to the template, but the email template (both migration 029 and 034 versions) only renders 5: `date`, `total_revenue`, `new_enrollments`, `sessions_held`, `absent_count`. The remaining 6 variables (`payment_details`, `payment_methods`, `instructors_list`, `attendance_rate`, `payment_count`, `unpaid_count`) are computed, fetched, and formatted but **never used** in the email body. They ARE used in the PDF attachment, but the email and PDF have different variable sets with no coordination.

**Acceptance**:
1. **Given** the daily report is sent, **When** the email body is rendered, **Then** only variables actually present in the template body/subject should be computed.
2. **Given** the PDF uses `payment_details`, `payment_methods`, `instructors_list`, `attendance_rate`, `payment_count`, `unpaid_count`, **When** the email template is updated, **Then** these should be available for email body too, OR the template should be revised to include them.

### User Story 6 — Scheduler does not double-send after restart (P2)

**Bug Found**: `last_daily`, `last_weekly`, `last_monthly` are Python in-memory variables. If the server restarts during the 5-minute trigger window, these guards reset to `None`, and the scheduler may re-send reports already dispatched the same day.

**Acceptance**:
1. **Given** the server restarts at 19:58 (2 minutes before the 20:00 daily report window), **When** the scheduler resumes and reaches 20:00–20:05, **Then** it must not re-send if the report was already sent before restart.
2. **Fix**: Persist `last_sent` to a DB table or use `notification_logs` to check if a report was already sent today.

### User Story 7 — Manual HTTP trigger exists for on-demand reports (P2)

**Bug Found**: There is no HTTP endpoint to trigger daily/weekly/monthly reports manually. The only way to send a report is to wait for the scheduler window. No `/api/v1/notifications/reports/daily` endpoint exists.

**Acceptance**:
1. **Given** an admin user, **When** calling `POST /api/v1/notifications/reports/daily`, **Then** the daily report is sent immediately and asynchronously.
2. **Given** an admin user, **When** calling `POST /api/v1/notifications/reports/weekly`, **Then** the weekly report is sent.
3. **Given** an admin user, **When** calling `POST /api/v1/notifications/reports/monthly`, **Then** the monthly report is sent.

---

## Requirements

### Functional Requirements

- **FR-001**: Daily report attendance counts must use only the actual `AttendanceStatus` domain values (`present`, `absent`, `cancelled`). Remove the `late` and `excused` status filters from `_fetch_daily_aggregates()`. The present+late count becomes just `present`. The excused count is removed. No DB migration needed.
- **FR-001b**: Daily report date-based queries must apply `COALESCE` fallbacks for nullable timestamp columns: use `COALESCE(Receipt.paid_at, Receipt.created_at)` for revenue/payment queries and `COALESCE(Enrollment.enrolled_at, Enrollment.created_at)` for enrollment count queries. Both the analytics service call and any inline queries must apply this fallback.
- **FR-002**: Monthly report date range must cover the **preceding full calendar month** when sent on day 1. On day 1, `month_start` must be the first day of the previous month, and `month_end` must be the last day of the previous month.
- **FR-003**: Weekly report date range must cover the **preceding 7 full days** (Monday–Sunday) when sent on Monday. `week_start` must be `today - timedelta(days=7)` and `week_end` must be `today - timedelta(days=1)`.
- **FR-004**: Weekly report "attendance rate" metric must be renamed to "Active Enrollment Rate" or recomputed from actual session attendance data to match the label.
- **FR-005**: Update the `daily_report` email template body to render all 11 computed variables. The template must include sections for payment details table, attendance rate, instructor list, payment methods breakdown, and unpaid enrollment count — matching the PDF attachment's content. Remove the sparse `<table>` from migration 029/034 and replace with the full HTML table already built in `send_daily_report()` as `payment_details_html`.
- **FR-006**: The system MUST provide REST API endpoints for manual on-demand triggering of daily, weekly, and monthly reports.
- **FR-007**: The system MUST support a `SCHEDULER_ENABLED` environment variable (default `true`) that prevents the scheduler from running when set to `false`.
- **FR-008**: Scheduler `last_sent` guards MUST be persisted (DB table or `notification_logs` check) to prevent double-sends after server restart.
- **FR-009a**: Create a typed Pydantic DTO (e.g., `DailyReportAggregateDTO`) to replace the `dict` return type of `_fetch_daily_aggregates()`.
- **FR-009b**: Move all aggregate queries from inside `_fetch_daily_aggregates()` into the analytics `financial_repository.py` (for revenue-related metrics) or a dedicated `reports_repository.py` under `app/modules/notifications/repositories/`. The service must call typed repository methods — no raw SQL in the service layer.
- **FR-010**: Weekly report must use `get_revenue_by_date()` from the analytics service for revenue, consistent with daily and monthly reports.
- **FR-011**: Report email bodies must be updated to include rich metrics (payment details table, attendance rate, instructor list, payment methods breakdown) matching the PDF attachment's content.

### Non-Functional Requirements

- **NFR-001**: Weekly and monthly report queries must follow the same pattern as daily — use `FinancialAnalyticsService.get_revenue_by_date()` for revenue (currently daily does, but weekly/monthly do their own thing).
- **NFR-002**: All f-string SQL interpolations in `_resolve_notification_recipients()` and `AdminSettingsRepository` must be replaced with parameterized queries (`:param` syntax).
- **NFR-003**: The scheduled report feature must have an HTTP trigger endpoint before any admin-facing UI integration.

### Key Entities

| Entity | File | Purpose |
|--------|------|---------|
| `ReportNotificationService` | `app/modules/notifications/services/report_notifications.py` | Fetches aggregates, renders templates, dispatches reports |
| `ReportScheduler` | `app/modules/notifications/services/report_scheduler.py` | Async polling loop (60s), delegates to `ReportNotificationService` |
| `daily_report_pdf.py` | `app/modules/notifications/pdf/daily_report_pdf.py` | ReportLab PDF for daily metrics |
| `BaseNotificationService._dispatch` | `app/modules/notifications/services/base_notification_service.py` | Sends email, logs result |

### Edge Cases

1. What happens when a report fires but no sessions were held and no payments received on that day? Current behavior: zero values are passed correctly, no crash — but email still renders empty tables. Acceptable.
2. What happens when `get_revenue_by_date` raises an exception? Daily report catches this with `logger.warning` and proceeds with `total_revenue = 0`. Weekly/monthly do the same. Acceptable.
2b. What happens when `COALESCE(paid_at, created_at)` is applied — does the created_at date match the business day the payment was processed? Yes, `created_at` is set at receipt creation time, which is the actual payment processing moment. Acceptable fallback.
3. What happens when the scheduler fires during a DB maintenance window? The `_dispatch` method catches exceptions at the log-update stage. The scheduler loop also has a top-level `try/except`. Acceptable.
4. What happens if a template name is changed or deleted? The scheduler checks `if not template or not template.is_active` and skips. Acceptable.
5. What happens on months with fewer than 31 days? Day-1 check `now.day == 1` handles this correctly — it fires on day 1 regardless of month length.

---

## Findings Summary

### Critical

| # | File | Line | Finding | Severity |
|---|------|------|---------|----------|
| 1 | `report_notifications.py` | 201–214 | Attendance query filters for `late` and `excused` statuses that don't exist in `AttendanceStatus` (`present`, `absent`, `cancelled` only). Counts always 0. | critical |
| 2 | `report_notifications.py` | 148–149 | Monthly report covers month-to-date (April 1–April 1 on day 1), not preceding full month. One day of data. | critical |

### High

| # | File | Line | Finding | Severity |
|---|------|------|---------|----------|
| 3 | `report_notifications.py` | 120–121 | Weekly report `week_start = today - timedelta(days=today.weekday())` on Monday gives `week_start = today` — covers 1 day, not 7. | high |
| 4 | `report_notifications.py` | 349–358 | Weekly "attendance_rate" computed from `BIAnalyticsService.get_retention_metrics()` — is actually active/total enrollment ratio, not attendance. Misleading label. | high |
| 5 | `report_notifications.py` | 71–83 | 6 of 11 daily report variables (`payment_details`, `payment_methods`, `instructors_list`, `attendance_rate`, `payment_count`, `unpaid_count`) are passed to template but never rendered in email body. | high |
| 6 | `report_scheduler.py` | 23–25 | `last_daily`, `last_weekly`, `last_monthly` guards are in-memory only — lost on restart, causing potential double-sends. | high |
| 7 | `report_scheduler.py` | — | No `SCHEDULER_ENABLED` env var to disable scheduler without code changes. | high |
| 8 | `report_notifications.py` | 166, 322, 366 | `_fetch_*_aggregates()` returns `dict` — violates Typed Contracts constitution rule (III). | high |

### Medium

| # | File | Line | Finding | Severity |
|---|------|------|---------|----------|
| 9 | `report_notifications.py` | 329–334 | Weekly report creates its own `FinancialAnalyticsService()` to get revenue — inconsistent with daily pattern (which also does this but only for revenue). Monthly does same. All three create a new analytics service instance. | medium |
| 10 | `base_notification_service.py` | 109–113 | `_resolve_notification_recipients` uses f-string SQL interpolation (`'{notification_type}' = ANY(...)`). Low risk (hardcoded values) but violates parameterized query convention. | medium |
| 11 | `admin_settings_repository.py` | 30, 42, 56–65, 97, 111, 131, 162, 172, 183 | All queries use f-string interpolation with potentially user-controlled values (email, notification_type, label). SQL injection vector. | medium |
| 12 | `report_notifications.py` | 280–289 | Raw SQL query for instructor list uses text() with proper parameter — inconsistent with neighboring f-string patterns. | low |

### Low

| # | File | Line | Finding | Severity |
|---|------|------|---------|----------|
| 13 | `report_notifications.py` | 429–441 | Disabled PARENT CODE PRESERVED (commented-out block for WhatsApp to parents). Dead code violation per constitution. | low |
| 14 | `daily_report_pdf.py` | all | PDF is daily-only. Weekly/monthly have no PDF. Acceptable per current business requirements, but inconsistent feature set. | low |
| 15 | `notification_service.py` | 43–142 | 7 deprecated delegation methods retained for backward compatibility. Constitution §VI requires zero tolerance for deprecated backward-compat methods. | low |

---

## Architecture Diagram

```
create_app() lifespan
  └─ asyncio.create_task(start_report_scheduler(make_service))
       └─ loop every 60s:
            ├─ check time window (DAILY_REPORT_HOUR ± 5min)
            ├─ check last_sent guards (in-memory)
            ├─ if daily due:
            │    └─ svc.report.send_daily_report()
            │         ├─ _repo.get_template_by_name("daily_report")
            │         ├─ _resolve_notification_recipients("daily_report")
            │         ├─ _fetch_daily_aggregates(today)
            │         │    ├─ FinancialAnalyticsService().get_revenue_by_date()
            │         │    ├─ Raw SQL: sessions held count
            │         │    ├─ Raw SQL: attendance stats (BUG: late/excused)
            │         │    ├─ Raw SQL: new enrollments
            │         │    ├─ Raw SQL: payments + methods + details
            │         │    ├─ Raw SQL: instructors list
            │         │    └─ Raw SQL: unpaid count
            │         ├─ generate_daily_report_pdf() [ReportLab]
            │         └─ for each recipient: _dispatch(EMAIL, ...)
            │
            ├─ if weekly due (Monday):
            │    └─ svc.report.send_weekly_report()
            │         ├─ _fetch_weekly_aggregates(week_start, week_end)
            │         │    ├─ FinancialAnalyticsService().get_revenue_by_date()
            │         │    ├─ Raw SQL: new enrollments
            │         │    └─ BIAnalyticsService().get_retention_metrics()
            │         └─ for each recipient: _dispatch(EMAIL, ...)
            │
            └─ if monthly due (day 1):
                 └─ svc.report.send_monthly_report()
                      ├─ _fetch_monthly_aggregates(month_start, month_end)
                      │    ├─ FinancialAnalyticsService().get_revenue_by_date()
                      │    └─ Raw SQL: new enrollments + active students
                      └─ for each recipient: _dispatch(EMAIL, ...)
```

---

## Assumptions

- WhatsApp is disabled for reports; email-only — confirmed by current code.
- The 13 notification types (including daily/weekly/monthly) are the complete set — no quarterly/annual reports in scope.
- The `notification_additional_recipients` table is the sole recipient source. `AdminSettingsRepository.get_enabled_admins_for_notification()` intentionally returns `[]`.
- PDF is daily-only by business requirement — no weekly/monthly PDF requested.
- The monthly date-window bug (month-to-date instead of preceding month) needs business confirmation of the intended behavior before fixing.
- The weekly boundary ambiguity (Monday-start vs Sunday-start) needs business confirmation before fixing.

---

## Success Criteria

- **SC-001**: Daily report attendance counts match actual domain values — no zero counts for non-existent statuses.
- **SC-002**: Monthly report covers exactly the preceding calendar month when sent on day 1.
- **SC-003**: Weekly report covers exactly the preceding 7 days (Monday–Sunday) when sent on Monday.
- **SC-004**: All unwritten template variables are either written into the template or removed from variable computation.
- **SC-005**: Scheduled reports can be manually triggered via REST API.
- **SC-006**: `SCHEDULER_ENABLED=false` prevents scheduler startup.
- **SC-007: Scheduler does not double-send any report type after server restart within the same period.
- **SC-008**: All `_fetch_*_aggregates()` methods return typed DTOs instead of `dict`.
- **SC-009**: All f-string SQL interpolations in notification domain are migrated to parameterized queries.
