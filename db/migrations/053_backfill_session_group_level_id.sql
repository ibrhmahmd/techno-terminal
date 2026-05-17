-- 053: Backfill group_level_id for existing sessions
-- Previously, sessions were created without setting group_level_id.
-- This joins sessions to group_levels on (group_id, level_number) to populate it.

UPDATE sessions s
SET group_level_id = gl.id
FROM group_levels gl
WHERE s.group_level_id IS NULL
  AND gl.group_id = s.group_id
  AND gl.level_number = s.level_number;

-- Log count of sessions that could not be backfilled
DO $$
DECLARE
    orphaned_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO orphaned_count
    FROM sessions
    WHERE group_level_id IS NULL;
    
    IF orphaned_count > 0 THEN
        RAISE NOTICE 'WARNING: % sessions have no matching GroupLevel record and remain NULL.', orphaned_count;
    END IF;
END $$;
