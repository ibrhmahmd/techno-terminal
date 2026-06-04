-- Make supabase_uid nullable so invited-but-unregistered users
-- can have NULL (allowing multiple NULLs in a UNIQUE constraint)
-- instead of empty strings (which collide).

ALTER TABLE users ALTER COLUMN supabase_uid DROP NOT NULL;

-- Convert existing empty-string rows to NULL
UPDATE users SET supabase_uid = NULL WHERE supabase_uid = '';

-- Rebuild the index; Postgres partial indexes on UNIQUE skip NULLs by default
DROP INDEX IF EXISTS idx_users_supabase_uid;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_supabase_uid ON users(supabase_uid);
