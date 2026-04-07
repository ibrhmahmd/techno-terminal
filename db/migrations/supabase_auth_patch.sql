-- Postgres SQL Migration: Strip passwords and apply Supabase mapping

-- 1. Remove the highly sensitive local password hashes
ALTER TABLE users DROP COLUMN password_hash;

-- 2. Add the authoritative Supabase mapping ID
-- We enforce UNIQUE constraint so no two users can share a Supabase identity
ALTER TABLE users ADD COLUMN supabase_uid VARCHAR(255) UNIQUE;
