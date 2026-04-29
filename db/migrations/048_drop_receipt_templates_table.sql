-- =============================================================================
-- MIGRATION 048: Drop unused receipt_templates table
-- Template content is never used for rendering (hardcoded Python templates used)
-- =============================================================================

-- Drop table (CASCADE removes trigger dependencies)
DROP TABLE IF EXISTS receipt_templates CASCADE;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify table is removed
SELECT 'receipt_templates removed: ' || 
    CASE WHEN COUNT(*) = 0 THEN 'YES' ELSE 'NO - still exists!' END AS verification
FROM information_schema.tables 
WHERE table_name = 'receipt_templates';
