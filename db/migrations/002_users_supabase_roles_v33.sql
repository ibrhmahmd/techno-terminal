-- 002 — Align users table with app v3.3 (Supabase auth + roles)
-- Apply ONCE per database that was created from schema before v3.3.
-- Prerequisites: PostgreSQL, existing techno_kids database.
--
-- After running: provision each user in Supabase Auth and set users.supabase_uid
-- (or use app/db/seed.py for the bootstrap admin).
--
-- Rollback: not automated; restore from backup if needed.

BEGIN;

-- 1) Role constraint: allow instructor; drop old check by common PG name pattern
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users
    ADD CONSTRAINT users_role_check CHECK (
        role IN ('admin', 'instructor', 'system_admin')
    );

-- 2) Supabase mapping column
ALTER TABLE users ADD COLUMN IF NOT EXISTS supabase_uid VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_supabase_uid ON users(supabase_uid);

-- 3) Remove local password storage (Supabase owns credentials)
ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

COMMIT;

-- 4) After every row has a real Supabase user id:
-- ALTER TABLE users ALTER COLUMN supabase_uid SET NOT NULL;
