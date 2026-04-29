-- =============================================================================
-- MIGRATION 047: Drop unused academic_categories and academic_years tables
-- These tables have no FK references, no app code usage, and no Python models
-- =============================================================================

-- Drop tables (CASCADE handles any unexpected dependencies)
DROP TABLE IF EXISTS academic_years CASCADE;
DROP TABLE IF EXISTS academic_categories CASCADE;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify tables are removed
SELECT 'academic_categories removed: ' || 
    CASE WHEN COUNT(*) = 0 THEN 'YES' ELSE 'NO - still exists!' END AS verification
FROM information_schema.tables 
WHERE table_name = 'academic_categories';

SELECT 'academic_years removed: ' || 
    CASE WHEN COUNT(*) = 0 THEN 'YES' ELSE 'NO - still exists!' END AS verification
FROM information_schema.tables 
WHERE table_name = 'academic_years';
