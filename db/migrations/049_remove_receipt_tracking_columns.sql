-- =============================================================================
-- MIGRATION 049: Remove receipt tracking columns
-- Dropping auto_generated, sent_to_parent, sent_at, parent_email columns
-- These are unused or being removed as part of receipt feature cleanup
-- =============================================================================

-- Drop columns
ALTER TABLE receipts 
    DROP COLUMN IF EXISTS auto_generated,
    DROP COLUMN IF EXISTS sent_to_parent,
    DROP COLUMN IF EXISTS sent_at,
    DROP COLUMN IF EXISTS parent_email;

-- Drop partial indexes (they were automatically dropped with columns, but be explicit)
DROP INDEX IF EXISTS idx_receipts_sent;
DROP INDEX IF EXISTS idx_receipts_auto_generated;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify columns are removed
SELECT 'Columns removed: ' || 
    CASE WHEN COUNT(*) = 0 THEN 'YES' ELSE 'NO - columns still exist!' END AS verification
FROM information_schema.columns 
WHERE table_name = 'receipts' 
  AND column_name IN ('auto_generated', 'sent_to_parent', 'sent_at', 'parent_email');
