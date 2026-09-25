# Recording the report period and guarding against concurrent runs

Type: grilling
Status: resolved
Blocked by:

## Question

How is a Delivery's report period stored, so that skip and retry can be keyed on (type, period, recipient)? Options include:

- a column on `notification_logs`
- a separate report-runs table
- a unique constraint

How do two overlapping triggers for the same period avoid sending twice? Options include a unique key, an advisory lock, or an insert-first claim.

Use `$codebase-design` and match the D+ and typed-contract rules in `AGENTS.md`.

## Answer

Add a `notification_logs.report_period_start` column, plus a partial unique index on `(template_id, report_period_start, recipient_contact)` covering `PENDING`/`SENT` rows. A run claims a recipient by inserting its row first. A `PENDING` row older than 15 minutes is taken over. This all goes through a `ReportDeliveryLedgerInterface` seam. Migration 081 applied to testing on 2026-09-25. Default accepted by the user on 2026-09-25.
