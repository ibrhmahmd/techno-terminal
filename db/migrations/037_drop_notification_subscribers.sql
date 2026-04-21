-- Migration: Drop notification_subscribers table
-- The subscriber logic is deprecated; reports now send to admins only

DROP TABLE IF EXISTS notification_subscribers CASCADE;

COMMENT ON TABLE notification_subscribers IS 'Table removed - notification subscribers feature discontinued';
