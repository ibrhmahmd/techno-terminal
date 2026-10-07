# Research: Daily Report Data & Template Fixes

## Background

No NEEDS CLARIFICATION items exist in this plan. All 5 bugs have unambiguous fixes verified against actual data models. This document records the design decisions validated during research.

## Decision Record

### Decision 1: Fix Instructor Query (Bug 1)

- **Decision**: Rename 3 columns in the raw SQL query at `report_notifications.py:272-278`
- **Rationale**: The existing query references non-existent column names (`e.name`, `s.instructor_id`, `s.date`), causing the instructors list to always be empty. The correct columns were verified against the actual SQLModel classes:
  - `Employee.full_name` instead of `Employee.name` (field found at `app/modules/hr/models/employee_models.py:18`)
  - `CourseSession.actual_instructor_id` instead of `CourseSession.instructor_id` (field found at `app/modules/academics/models/session_models.py:18`)
  - `CourseSession.session_date` instead of `CourseSession.date` (field found at `app/modules/academics/models/session_models.py:15`)
- **Alternatives considered**: None — this is a correction of incorrect column names, not a design choice.

### Decision 2: Payment Group Resolution (Bug 2)

- **Decision**: Resolve group name through `Payment.enrollment_id → Enrollment.group_id → Group.name` chain
- **Rationale**: The `Payment` model has no `group_id` column. The `AttributeError` from `payment.group_id` is silently caught, making `payment_details` always empty. The group must be reached through the enrollment relationship.
- **Import needed**: `from app.modules.enrollments.models.enrollment_models import Enrollment`
- **Alternatives considered**: Adding a `group_id` column to `payments` table — rejected because it would require a DB migration and redundant data storage when the relationship already exists through `enrollments`.

### Decision 3: Date Filter Alignment (Bug 3)

- **Decision**: Change payment query to join with `receipts` and filter by `receipts.paid_at` instead of `payments.created_at`
- **Rationale**: The revenue query (via `FinancialAnalyticsService`) uses `receipts.paid_at`. The payment detail query used `payments.created_at`, which means they can disagree for backdated entries. Both should use the same timestamp for consistency.
- **Import needed**: `from app.modules.finance.models.receipt import Receipt`
- **Alternatives considered**: Changing the revenue query to use `payments.created_at` — rejected because revenue is inherently tied to when payment was received (`paid_at`), not when the record was created.

### Decision 4: PDF B&W Redesign (Bug 4)

- **Decision**: Full rewrite of `daily_report_pdf.py` using only black text, white backgrounds, thin black borders, and very light gray (`#f5f5f5`) alternating rows
- **Rationale**: The current design uses colored backgrounds (green, blue, orange, purple) with white text, which renders as indistinguishable grays on B&W printers, making the report unreadable.
- **Alternatives considered**: Adding `@media print` CSS to PDF — not applicable (PDF is a fixed format, not HTML). Adding grayscale conversion at print time — not possible (PDF is pre-generated).

### Decision 5: Email HTML Print Styles (Bug 5)

- **Decision**: Add `<style>` block with `@media print` rules to the email HTML template; replace dark header backgrounds with bottom borders
- **Rationale**: Table headers with `background: #2c3e50; color: white` become invisible on B&W print. Using `border-bottom: 2px solid black` instead ensures headers are readable in all print modes.
- **Alternatives considered**: Removing all styling — rejected because color email clients still benefit from visual hierarchy. Moving template to a separate file — rejected because it's a small inline template used only in this one method.

### Decision 6: Test Strategy

- **Decision**: Add 3 tests to `TestReportNotifications` class in `tests/test_notifications.py` using `MockNotificationRepository` + monkeypatching `_fetch_daily_aggregates`
- **Rationale**: The `_fetch_daily_aggregates` method uses its own database sessions, making it difficult to mock at the session level. Testing at the `send_daily_report` level with mocked aggregate data validates the template rendering, recipient resolution, and dispatch flow.
- **Alternatives considered**: Using `_MockSession` pattern from enrollment tests — rejected because `_fetch_*` methods open their own sessions internally, not through the injected repo.

### Decision 7: No New Data Entities

- **Decision**: Skip `data-model.md` and `contracts/` — no new database entities, DTOs, or API contracts are introduced
- **Rationale**: All 5 bugs are fixes to existing code. No new tables, columns, API endpoints, or data structures are created.
