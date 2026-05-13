-- Migration 051: Add retry columns to notification_logs
-- Supports automatic and manual retry of failed notification dispatches
-- Retry strategy: auto 3x (1min / 5min / 30min), manual retry from notification log

ALTER TABLE notification_logs
  ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP;
