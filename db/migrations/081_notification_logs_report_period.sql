-- Migration: 081_notification_logs_report_period
-- Description: Add report-period claims for reliable scheduled report delivery
-- Date: 2026-09-25
-- Related: Scheduled report delivery ledger

ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS report_period_start DATE;
CREATE UNIQUE INDEX IF NOT EXISTS uq_notification_logs_report_delivery
    ON notification_logs (template_id, report_period_start, recipient_contact)
    WHERE report_period_start IS NOT NULL AND status IN ('PENDING', 'SENT');
