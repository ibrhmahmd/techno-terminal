# Feature Specification: Scheduled Report Audit

**Feature Branch**: `012-scheduled-report-audit`  
**Created**: 2026-05-18  
**Status**: Draft  
**Input**: User description: "notification module focusing on the reports features daily, weekly, monthly — review its current implementation and audit its logic, making sure it's aligning with the business requirements"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin receives daily business summary email (Priority: P1)

An admin wants to receive a reliable, comprehensive daily business summary every evening at a configured time. The report includes total revenue collected that day, new student enrollments, sessions held, absent count, attendance rate, payment transactions broken down by method, and a full payment details table. A PDF version is attached to the email.

**Why this priority**: This is the primary operational report. School owners and managers rely on it to close out each business day. If reports are missed or incomplete, day-end financial reconciliation becomes manual and error-prone.

**Independent Test**: Trigger a daily report manually and verify the email lands in the inbox with all expected sections and a valid PDF attachment. Revenue, attendance, enrollment, and payment numbers can each be cross-checked against source data for accuracy.

**Acceptance Scenarios**:

1. **Given** daily reports are enabled and a valid email template named `daily_report` exists, **When** the scheduler fires at the configured time, **Then** every additional recipient receives an email with the full daily summary and a correctly formatted PDF attachment.
2. **Given** the daily report runs, **When** there were zero payments and zero sessions on a given day, **Then** the email still sends without error, showing appropriate zero-value indicators instead of omitting sections.
3. **Given** the daily report is triggered, **When** PDF generation raises an exception, **Then** the email still sends without the attachment and the error is logged for operator attention.
4. **Given** no additional recipients are configured, **When** the scheduler fires, **Then** the notification falls back to the configured fallback email and an alert is logged in `notification_logs`.

---

### User Story 2 - Admin receives weekly business summary (Priority: P2)

An admin wants a weekly rollup report every Monday morning that summarizes the previous week's total revenue and new student signups, providing a quick health check without reading five separate daily emails.

**Why this priority**: Weekly reports give leadership a compressed weekly snapshot. Without a reliable Monday report, admins must manually aggregate daily emails to answer simple questions like "how did last week compare to the week before?"

**Independent Test**: Manually disable any safeguards that restrict scheduling to Monday and fire a weekly report. Verify that revenue and new-student totals reflect the exact 7-day window the report claims to cover.

**Acceptance Scenarios**:

1. **Given** weekly reports are enabled and the day is Monday, **When** the scheduler reaches the weekly trigger window, **Then** a report covering the previous 7 days (Monday–Sunday) is sent to all configured recipients.
2. **Given** the scheduler falls on a non-Monday day, **When** the 5-minute scheduler window opens, **Then** `send_weekly_report` is not called.

---

### User Story 3 - Admin receives monthly business summary (Priority: P2)

An admin wants a monthly summary on the first day of each month showing total monthly revenue, total new enrollments for the month, and currently active student count. This supports monthly board reviews and financial close-out.

**Why this priority**: Monthly reports are required for financial close-out, VAT reporting, and owner review meetings. A missed report means an entire month must be reconstructed from transaction logs.

**Independent Test**: Set `today.day == 1` (or mock date), trigger the monthly report function, and verify revenue totals, enrollment counts, and active-student counts reflect the calendar month the report claims to cover.

**Acceptance Scenarios**:

1. **Given** monthly reports are enabled and the current day is the first of the month, **When** the scheduler fires, **Then** a report covering the calendar month-to-date (1st of previous month through today) is sent.
2. **Given** the current day is day 2 or later, **When** the scheduler fires, **Then** `send_monthly_report` is not called.

---

### User Story 4 - Scheduler survives server restarts without duplicate sends (Priority: P2)

The report scheduler runs as an in-memory asyncio task started at app lifespan. If the server restarts at 19:58 (2 minutes before the trigger window) while the scheduler was still healthy before shutdown, the `last_sent` guards were lost, and the new task would re-send reports that were already sent that period.

**Why this priority**: Scheduled reports that arrive twice in a period (double-charged daily totals, double-counted enrollments) are worse than no report at all. Managers making decisions on duplicated data cause cascading errors.

**Independent Test**: Set the scheduler to a time 2 minutes in the future; start the app, verify the first run fires once. Do not reload. Note: this scenario is difficult to perfectly unit-test — the guard is in-memory by design. The validation path proves correct behaviour via the code path.

**Acceptance Scenarios**:

1. **Given** the scheduler already sent a daily report today, **When** the server restarts and the new scheduler instance reaches the trigger window, **Then** it does NOT re-send the daily report.

---

### User Story 5 - Admin manages scheduled report subscriptions via REST API (Priority: P3)

An admin can review which notification types are enabled (including `daily_report`, `weekly_report`, `monthly_report`), toggle any report type on or off, add or remove additional email recipients, and configure which notification types each recipient should receive — all through the `/api/v1/notifications/admin` REST API.

**Why this priority**: Without a working admin UI or API, scheduling requires a direct database edit, which is error-prone and non-auditable. Enabling/disabling report types per recipient type is a basic operational requirement.

**Independent Test**: Make a GET request to `/api/v1/notifications/admin/settings/me`, verify all 13 notification types are listed with their `is_enabled` defaults. Toggle `daily_report` to `false`, verify a second GET shows the updated state.

**Acceptance Scenarios**:

1. **Given** an admin user, **When** calling `GET /api/v1/notifications/admin/settings/me`, **Then** the response includes `daily_report`, `weekly_report`, and `monthly_report` with their current `is_enabled` status.
2. **Given** daily reports are enabled, **When** an admin toggles `daily_report` to disabled, **Then** the toggle endpoint returns the updated setting and the scheduler no longer sends daily reports.

---

### User Story 6 - Report data accuracy against source analytics (Priority: P1)

The daily report's revenue figure must match `get_revenue_by_date`. The weekly report's revenue figure must cover exactly 7 days ending on the report date. The monthly report's revenue must cover the calendar month. Off-by-one errors or wrong date windows silently produce wrong business decisions.

**Why this priority**: If the revenue number on a daily report is off by even 10%, a manager may take incorrect action (e.g., authorize an extra expense, flag a payment discrepancy). Accuracy is the single most important quality property of automated reports.

**Independent Test**: For a known date range, insert known payments/receipts, run the aggregate fetcher, and compare the returned numbers against values returned by the analytics service for the same date range.

**Acceptance Scenarios**:

1. **Given** a date with known payments totaling 1,000 EGP, **When** `_fetch_daily_aggregates(date)` is called, **Then** `total_revenue` equals the exact sum of net revenues for that date.
2. **Given** today is Monday March 9, **When** `_fetch_weekly_aggregates(week_start, week_end)` is called, **Then** `week_start` is March 2 and `week_end` is March 9 — no day is double-counted or missed.
3. **Given** today is April 1, **When** `_fetch_monthly_aggregates(month_start, today)` is called, **Then** the revenue covers January through March 31, not April 1.

---

### Edge Cases

- What happens when the scheduler runs but no template with the expected name (`daily_report`, `weekly_report`, `monthly_report`) exists in the database?
- What happens when a report template is deactivated by an admin mid-day — is the in-flight report already dispatched, or is it silently dropped?
- What happens when the scheduler fires during a database maintenance window from the 60-second polling loop?
- What happens when an admin sets an invalid day-of-month in a future session-level configuration (if day-end configuration is added) relative to a month with fewer days?
- What happens if `get_revenue_by_date` returns zero results for a period that does have transactions — is that treated as revenue or as an error?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST send a daily business summary email on every active day at a configurable time, including revenue, enrollments, session count, attendance rate, payment details, and unpaid enrollment count.
- **FR-002**: The system MUST send a weekly business summary email every Monday, covering the previous 7 days including revenue and new student signups.
- **FR-003**: The system MUST send a monthly business summary email on the first day of every month, covering the preceding calendar month including total revenue, new enrollments, and active student count.
- **FR-004**: Report recipients MUST be resolved from the `notification_additional_recipients` database table by matching the notification type; if no valid recipients are found, the system MUST use a configured fallback email address.
- **FR-005**: The daily report MUST include a PDF attachment generated by the PDF service with revenue cards, session metrics, payment details, and attendance rate.
- **FR-006**: Admins MUST be able to view and toggle daily, weekly, and monthly report subscriptions via the admin notification settings API.
- **FR-007**: The system MUST support a `SCHEDULER_ENABLED` environment variable that disables all automated report scheduling when set to `false`, without requiring a code change or database migration.
- **FR-008**: The system MUST provide an HTTP trigger (manual run endpoint or equivalent) so daily, weekly, and monthly reports can be triggered on demand by an admin without waiting for the scheduler window.
- **FR-009**: The daily report aggregate fetcher MUST match the revenue source used by the Finance Analytics service (receipt `paid_at` date filtering aligned with session boundaries, not payment `created_at` timestamps).
- **FR-010**: The weekly report aggregate MUST cover exactly 7 calendar days ending on the report date (i.e., the Monday the report fires for covers Sunday–Saturday or Monday–Sunday — [NEEDS CLARIFICATION: week-wrap-around policy not specified — does the report week end on Saturday or Sunday?]).
- **FR-011**: The monthly report aggregate MUST cover a complete, consecutive calendar month — [NEEDS CLARIFICATION: does month-end exactly report on the previous full calendar month, or does it fire on day 1 for the just-completed month?].
- **FR-012**: The scheduler MUST log every report dispatch成败 to `notification_logs` with template_id, channel, recipient_type, recipient_contact, status, and sent_at timestamp.
- **FR-013**: Report emails MUST use the EMAIL channel only — the WhatsApp channel is disabled for report delivery in the current implementation.

### Key Entities

- **ReportNotificationService**: Service class that fetches aggregate data and dispatches scheduled report emails. Fetches data from Finance Analytics, Attendance, Academics, and direct SQL queries. Pure data aggregation — no scheduling logic.
- **ReportScheduler**: Async polling loop that checks every 60 seconds whether a report window is open and delegates to `ReportNotificationService`. Currently in-memory only with no persistence guard.
- **DailyReportPDFGenerator**: PDF generator using ReportLab that formats daily metrics into a styled two-page document with summary cards, payment details table, and footer.
- **NotificationTemplate** (`notification_templates` table): Named templates (`daily_report`, `weekly_report`, `monthly_report`) controlling which report types are active and what HTML body is sent.
- **NotificationLog** (`notification_logs` table): Audit trail for every dispatch attempt — required for verifying delivery and debugging missing reports.
- **NotificationAdditionalRecipients** (`notification_additional_recipients` table): Per-recipient email opt-in; each recipient can be scoped to specific notification types or receive all types.
- **AdminNotificationSettings** (`admin_notification_settings` table): Per-notification-type enable/disable flag per admin. Controls whether the scheduler sends a given report type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Daily reports are sent within 5 minutes of their configured time in 99% of days over any 30-day window [NEEDS CLARIFICATION: "within 5 minutes of configured time" vs "within a 5-minute window centered on the configured time" — scheduler currently uses a window-based check, not an exact-time trigger].
- **SC-002**: Weekly reports are delivered every Monday without a missed Monday over a rolling 3-month window.
- **SC-003**: Monthly reports are delivered on the first of each month for 100% of months over a 6-month window.
- **SC-004**: Revenue figures in the daily report match the Finance Analytics `get_revenue_by_date` output for the same date with 100% accuracy on every run.
- **SC-005**: When a report cannot be sent for any reason, at least one fallback recipient and one `notification_logs` entry with status `FAILED` is created within the same dispatch attempt.
- **SC-006**: Admin notification settings toggles for `daily_report`, `weekly_report`, and `monthly_report` take effect within 60 seconds of the REST API call.
- **SC-007**: The scheduler does not send the same daily/weekly/monthly report more than once per period across any observed 30-day window.
- **SC-008**: Report email delivery succeeds (email `SENT` in `notification_logs`) for at least 95% of dispatch attempts over any rolling 30-day window.

## Assumptions

- The current implementation is email-only. WhatsApp for reports is explicitly disabled and out of scope.
- Scheduler configuration (report time, enabled/disabled flags) is read from environment variables and managed through the admin settings REST API; there is no session-level per-admin `notify_type` configuration for scheduled reports.
- The weekly report's report period covers the 7 days ending on the day the report fires — this is the current behaviour but needs explicit business confirmation or a configuration option.
- Scheduler state (`last_daily`, `last_weekly`, `last_monthly`) is in-memory only. Business acceptable risk for restarts is assumed low (once per week/month respectively).
- Three report types (daily, weekly, monthly) are the only scheduled reports currently in scope — no quarterly, annual, or ad-hoc custom report schedules exist.
- The `SCHEDULER_ENABLED` environment variable is assumed desired as a kill-switch and will be implemented as part of any future refactor; it does not currently exist in the codebase.
- PDF is generated daily only. The business does not currently request PDF for weekly or monthly, so this feature is out of scope for a weekly/monthly PDF attachment.
- Weekly/monthly report PDFs have no template today — this is known and acceptable until business requirements change.
- The monthly report currently queries `get_revenue_by_date(month_start, month_end)` where `month_end` is `today`. This covers the month-to-date range. Whether it SHOULD cover the preceding full month (e.g., on April 1 send March's report) requires business confirmation.
- PDF quality is out of scope. The current PDF uses ReportLab with B&W theme. No brand revision requested at this time.
