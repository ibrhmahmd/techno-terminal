# Research: Daily Report Redesign & Debtors Data

## Decisions

### 1. Precision Engine Email Design
- **Decision**: Full HTML email redesign following `docs/DESIGN_SYSTEM.md`
- **Rationale**: Move from generic Arial/border-based layout to the established Precision Engine visual language
- **Key constraints**: No CSS borders for sectioning (tonal layering via background-color shifts), Space Grotesk @import for headings, Inter for body, Power Gradient for KPIs, teal/amber status chips, @media print for B&W printing

### 2. Debtors Data Sources
- **Decision**: Reuse existing analytics services (`FinancialAnalyticsService`, `AcademicAnalyticsService`) via module root `__init__.py`
- **Rationale**: These already query `v_enrollment_balance` view correctly — no new queries needed for top debtors, outstanding by group, or today's unpaid attendees
- **Constitution check**: Services import through module `__init__.py` (allowed cross-slice orchestration pattern)

### 3. Tomorrow's Unpaid Attendees Query
- **Decision**: New query in `ReportsRepository` — join `sessions` (session_date = tomorrow) with `v_enrollment_balance` (balance < 0)
- **Rationale**: No existing query covers this specific case. The repo is the right place since `ReportsRepository` already owns daily report queries
- **Pattern**: Follows SQLModel `text()` parameterized query pattern used in all existing repo methods

### 4. Test Email Mechanism
- **Decision**: CLI script (`scripts/test_report_email.py`), no auth
- **Rationale**: Developer preview tool — not an API endpoint. Runs standalone with hardcoded date 2026-05-24
- **Pattern**: Follows existing `scripts/test_daily_report_smoke.py` pattern (argparse, subprocess for JWT if needed)

### 5. PDF Unchanged
- **Decision**: No changes to `daily_report_pdf.py`
- **Rationale**: Already B&W and printer-friendly. Spec explicitly requires it stays unchanged

## Architectural Notes

- **Email template storage**: The `notification_templates` table stores raw HTML with `{{variable}}` placeholders. The `_build_variables()` method generates the complex HTML tables as rendered HTML strings (not template markup). This pattern continues — new debtors sections will be generated as HTML in `_build_variables()` and passed as variables.
- **Template body update**: Via a new migration file `058_update_daily_report_precision_engine.sql` following the existing pattern (UPDATE statement with inline HTML body).
- **DailyReportAggregateDTO**: Existing DTO needs new fields added for debtors and tomorrow data.
- **TomorrowPreviewDTO**: New DTO to hold tomorrow's preview data structure.
- **CLI script**: `scripts/test_report_email.py` imports `ReportNotificationService` directly, creates its own session, generates report for 2026-05-24, and dispatches to a provided email address.
