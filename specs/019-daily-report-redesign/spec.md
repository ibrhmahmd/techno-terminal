# Feature Specification: Daily Report Redesign & Debtors Data

**Feature Branch**: `019-daily-report-redesign`  
**Created**: 2026-05-24  
**Status**: Draft  
**Input**: "Redesign daily report email to Precision Engine design system. Add today's unpaid attendees, tomorrow's unpaid attendees, debtors snapshot, tomorrow's preview. Send test email with new design first before implementing full changes. PDF stays black & white for printing."

## Clarifications

### Session 2026-05-24

- Q: Should the test email endpoint require admin auth? → A: No auth required — it is a pure visualization/preview tool for developers
- Q: Should the test email use mock data or real data? → A: Real data for 2026-05-24 (hardcoded reference date)
- Q: Should the test email be an HTTP endpoint or CLI script? → A: CLI script (`python scripts/test_report_email.py`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Receives Redesigned Daily Email (Priority: P1)

A center admin opens their email and sees the daily operations report redesigned with the Precision Engine design system — Space Grotesk headings, Inter body text, deep slate/teal palette, tonal sectioning (no borders), status chips, and Power Gradient metrics. The email is visually sophisticated, readable on desktop and mobile, and communicates data clearly.

**Why this priority**: The visual redesign is the primary deliverable — it sets the new look-and-feel baseline for all subsequent notification emails.

**Independent Test**: Can be verified by sending a single test email to any admin address with mock data and confirming the HTML renders correctly in Gmail, Outlook, and Apple Mail.

**Acceptance Scenarios**:

1. **Given** the daily report is generated, **When** the email is rendered, **Then** the HTML uses Space Grotesk for all headings and Inter for body text (loaded via CSS `@import`)
2. **Given** the daily report email is viewed on screen, **When** sections appear, **Then** sectioning is achieved through background-color shifts (tonal layering) — NOT through CSS borders or horizontal rules
3. **Given** a key metric (revenue, attendance rate), **When** it is displayed, **Then** it appears on a tonal card with subtle gradient background (Power Gradient from `#131b2e` to `#000000`)
4. **Given** a debt/alert status (unpaid student, low attendance), **When** the status chip renders, **Then** it uses `secondary_container` (teal) for paid/active status and `error_container` (amber) for debt/inactive status
5. **Given** the email is printed, **When** the user prints, **Then** the `@media print` styles use black text on white background with simple borders for tables

---

### User Story 2 - Admin Sees Debtors Data in Daily Email (Priority: P1)

An admin opens the daily report and sees a Debtors Alert section at the top: total outstanding debt (EGP), number of debtors, top 5 debtors by name and amount, and today's unpaid attendees (students who attended today but have outstanding balance). The admin can immediately identify which families need follow-up.

**Why this priority**: This is the most actionable data — staff need to know who owes and who attended today without paying.

**Independent Test**: Can be verified by generating a report for a day where specific students attended with negative balance, and confirming their names appear in the appropriate section.

**Acceptance Scenarios**:

1. **Given** there are students with negative balance who attended today, **When** the daily report is generated, **Then** they appear in a "Today's Unpaid Attendees" subsection with student name, group, and amount owed
2. **Given** there are top debtors across the center, **When** the report is generated, **Then** the top 5 debtors by total outstanding are listed with name and amount
3. **Given** total outstanding debt is calculated, **When** the report is generated, **Then** the aggregate total and debtor count are displayed prominently in the Debtors Alert section
4. **Given** outstanding debt is grouped by group, **When** the report is generated, **Then** each group with debt is listed with group name, number of debtors, and total outstanding

---

### User Story 3 - Admin Sees Tomorrow's Preview with Unpaid Alert (Priority: P2)

An admin opens the daily report and sees a "Tomorrow's Preview" section showing how many sessions are scheduled, how many students are expected, and — critically — which of tomorrow's expected attendees currently have outstanding debt. The admin can pre-emptively send reminders or prepare for payment collection.

**Why this priority**: Proactive debt management prevents revenue loss and reduces on-the-day friction.

**Independent Test**: Can be verified by generating a report when sessions exist for tomorrow and certain enrolled students have negative balance — those students appear in the unpaid-for-tomorrow subsection.

**Acceptance Scenarios**:

1. **Given** there are sessions scheduled for tomorrow, **When** the daily report is generated, **Then** the "Tomorrow's Preview" section shows the count of sessions and total expected students
2. **Given** some of tomorrow's expected attendees have negative balance, **When** the report is generated, **Then** they appear in a subsection with their name, group, session time, and amount owed
3. **Given** tomorrow has no sessions scheduled, **When** the report is generated, **Then** the "Tomorrow's Preview" section displays "No sessions scheduled tomorrow"

---

### User Story 4 - Developer Sends Test Email with New Design (Priority: P1)

Before deploying the redesigned daily report to all recipients, a developer can run a CLI script to send a test email to a single address with real data for a hardcoded reference date (2026-05-24) to verify the new HTML layout, typography, colors, and sections render correctly across email clients. No authentication is required — it is a development-only preview tool.

**Why this priority**: The user explicitly requested test-email-first — validating the design before full rollout prevents sending broken or poorly-rendered emails to all admins.

**Independent Test**: Can be verified by running the CLI script and confirming the email arrives with the Precision Engine HTML rendered correctly.

**Acceptance Scenarios**:

1. **Given** the CLI script `python scripts/test_report_email.py`, **When** run with a recipient email, **Then** the new Precision Engine HTML is sent to that email using real data for 2026-05-24
2. **Given** the test email arrives, **When** opened in Gmail, **Then** all sections render correctly with proper fonts, colors, and spacing
3. **Given** the 2026-05-24 data includes debtors and tomorrow's preview, **When** the email is rendered, **Then** those sections appear with correct data
4. **Given** the PDF is generated alongside the test email, **When** attached, **Then** the PDF remains black & white (unchanged from current design)

---

### Edge Cases

- What happens when there are zero transactions/attendance for the day? The report should show "No data" placeholders rather than empty sections
- What happens when there are zero debtors? The Debtors Alert section should show "No outstanding debt" rather than an empty table
- What happens when email clients block web fonts (`@import`)? The email should fall back gracefully to system fonts (Arial/Helvetica for body, Georgia for headings)
- What happens when the PDF attachment is too large (many payment rows)? The generation should not crash — ReportLab handles large tables
- What happens on public holidays with no sessions? Tomorrow's Preview shows "No sessions scheduled" and the report is still sent with minimal data

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a new email HTML template for the daily report that follows the Precision Engine design system
- **FR-002**: Email HTML MUST load Space Grotesk and Inter via CSS `@import` with fallback to system fonts
- **FR-003**: Sectioning in the email MUST use background-color shifts (tonal layering) instead of CSS borders or horizontal rules
- **FR-004**: Key metric cards MUST use a subtle linear gradient background (Power Gradient)
- **FR-005**: Status indicators (paid/unpaid, active/inactive) MUST use tonal chip styling with teal for positive and amber for alert states
- **FR-006**: The email MUST include `@media print` styles that render as black-on-white with simple borders
- **FR-007**: System MUST query today's unpaid attendees (students who attended today with negative balance) and include them in the Debtors Alert section
- **FR-008**: System MUST query top debtors across the center (limited to top 5) with name and outstanding amount
- **FR-009**: System MUST query outstanding debt grouped by active group with group name, debtor count, and total
- **FR-010**: System MUST query tomorrow's sessions and identify which expected attendees have negative balance
- **FR-011**: System MUST include a "Tomorrow's Preview" section with session count, expected student count, and unpaid attendee alerts
- **FR-012**: System MUST provide a CLI script (`scripts/test_report_email.py`) that sends a test email with the new design and real data for 2026-05-24 to a single recipient for validation
- **FR-013**: The PDF attachment generated alongside the email MUST remain unchanged (black & white, printer-friendly)
- **FR-014**: The email MUST render correctly in Gmail, Outlook, and Apple Mail on both desktop and mobile
- **FR-015**: The PDF MUST still be attached to the daily report email (same as current behavior)
- **FR-016**: All new debtors data must come from the existing `v_enrollment_balance` database view (no new migrations)
- **FR-017**: The tomorrow's unpaid attendees query MUST join tomorrow's sessions with `v_enrollment_balance` where balance is negative
- **FR-018**: Email template variables MUST include all new data fields so the template engine can render them
- **FR-019**: The template body (stored in `notification_templates` table) MUST be updated with the new Precision Engine HTML

### Key Entities *(data involved)*

- **DailyReportAggregateDTO**: Existing DTO that holds all daily metrics — needs new fields for total outstanding debt, debtor count, top debtors list, today's unpaid attendees, tomorrow's preview data, and tomorrow's unpaid attendees
- **UnpaidAttendeeDTO** (existing): Student ID, name, parent name, phone, total balance — used for today's unpaid attendees and tomorrow's unpaid alerts
- **TopDebtorDTO** (existing): Student ID, name, parent name, phone, total outstanding — used for top 5 debtors
- **OutstandingByGroupDTO** (existing): Group ID, name, course name, student count with balance, total outstanding — used for debt by group
- **TomorrowPreviewDTO** (new): Date, session count, expected student count, unpaid attendees list — used for tomorrow's preview section
- **NotificationTemplate**: Existing model that stores email body HTML and variable list — needs updated body for Precision Engine design

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can visually confirm the new Precision Engine design renders correctly in a test email before any automated dispatch occurs
- **SC-002**: Debtors data (today's unpaid + top debtors + outstanding by group) appears in the email within 5 minutes of report generation
- **SC-003**: Tomorrow's unpaid alert identifies students with sessions tomorrow who owe money, with 100% accuracy against the `v_enrollment_balance` view
- **SC-004**: The email renders without visual layout breaks in Gmail, Outlook web, and Apple Mail
- **SC-005**: The PDF attachment remains visually identical to the current version (black & white, same layout/data)
- **SC-006**: The redesigned email uses zero CSS borders for sectioning — all spatial division is achieved via background-color shifts
- **SC-007**: All 15 existing notification tests continue to pass unchanged

## Assumptions

- The Precision Engine design system is defined in `docs/DESIGN_SYSTEM.md` and all email styling decisions are derived from it
- Existing data sources (`v_enrollment_balance` view, `AcademicAnalyticsService`, `FinancialAnalyticsService`) are sufficient — no new DB migrations are needed
- The PDF generation (`daily_report_pdf.py`) is already black & white and printer-friendly — no changes required
- Email clients' CSS support: `background-color`, `@import` for web fonts, inline styles, and `@media print` are supported by all target clients
- The test email mechanism is a CLI script (`scripts/test_report_email.py`) — no authentication, no HTTP endpoint
- The notification template body in the database will be updated via a new migration (SQL `UPDATE` statement)
- Gmail may clip emails over 102KB — the template must stay within reasonable size limits
