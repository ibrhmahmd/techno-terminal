-- =============================================================================
-- Migration 081: Scheduled report delivery claims
-- Date: 2026-09-25
-- Related: ISSUES.md #1 (scheduled reports not sent),
--          .scratch/reliable-report-delivery/issues/09-record-report-period.md
--
-- Adds the Report Period to notification_logs so that each scheduled report
-- Delivery is keyed on (template_id, report_period_start, recipient_contact).
-- The partial unique index is the claim: a trigger inserts a PENDING row
-- before sending, so two overlapping triggers can never both send to the same
-- recipient for the same period. FAILED rows fall outside the index, so a
-- failed recipient can be retried. The code in
-- app/modules/notifications/repositories/report_delivery_ledger.py matches
-- the index by its exact name.
--
-- Only scheduled-report deliveries set report_period_start. Every other
-- notification leaves it NULL and is unaffected by the index.
--
-- Safety:
--   * Additive only. Existing rows get NULL, so the unique index cannot
--     conflict with existing data.
--   * Compatible with code deployed before this migration (which does not
--     know about the column). Apply this migration BEFORE deploying code that
--     maps NotificationLog.report_period_start, or every log insert fails.
--   * lock_timeout makes the script fail fast instead of queueing writes
--     behind a long-held lock; if it times out nothing changes, rerun it.
--
-- Rollback:
--   DROP INDEX IF EXISTS uq_notification_logs_report_delivery;
--   ALTER TABLE notification_logs DROP COLUMN IF EXISTS report_period_start;
--
-- Applied:
--   testing (qugffjtucavdseczbata): 2026-09-25
--   production (srbppkcvrgioneitktdj): pending
-- =============================================================================

SET lock_timeout = '5s';

BEGIN;

ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS report_period_start DATE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_notification_logs_report_delivery
    ON notification_logs (template_id, report_period_start, recipient_contact)
    WHERE report_period_start IS NOT NULL AND status IN ('PENDING', 'SENT');

COMMIT;
