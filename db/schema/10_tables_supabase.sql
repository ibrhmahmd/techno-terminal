-- =============================================================================
-- SUPABASE SYSTEM TABLES
-- Tables managed by or related to Supabase platform features
-- Note: Many Supabase tables (auth.*, storage.*) are in separate schemas
-- =============================================================================

-- =============================================================================
-- REALTIME SUBSCRIPTION
-- Supabase Realtime subscription tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS subscription (
    id BIGSERIAL PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    entity TEXT NOT NULL,
    filters JSONB,
    claims JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE subscription IS 'Supabase Realtime subscription tracking (system table)';

-- =============================================================================
-- HOOKS
-- Supabase Hooks for external integrations
-- =============================================================================
CREATE TABLE IF NOT EXISTS hooks (
    id BIGSERIAL PRIMARY KEY,
    hook_name TEXT NOT NULL,
    hook_table TEXT NOT NULL,
    hook_timing TEXT NOT NULL,
    hook_events TEXT[] NOT NULL,
    url TEXT NOT NULL,
    headers JSONB DEFAULT '{}',
    payload JSONB,
    retries INTEGER DEFAULT 3,
    timeout_ms INTEGER DEFAULT 5000,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hooks IS 'Supabase Hooks configuration for external integrations';

-- =============================================================================
-- NOTES
-- 
-- The following Supabase schemas are managed by Supabase and not included here:
-- - auth.* (authentication, users, sessions)
-- - storage.* (file storage buckets and objects) - public.objects table exists
-- - realtime.* (realtime publication configuration)
-- 
-- The public schema tables buckets and objects are Supabase Storage tables
-- in the public schema and are referenced in the application.
-- =============================================================================

-- Supabase Storage tables (if they need to be documented)
-- These are typically auto-created by Supabase Storage extension

-- buckets table (documented for reference)
-- Note: Usually auto-created by Supabase Storage
CREATE TABLE IF NOT EXISTS buckets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    owner UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    public BOOLEAN DEFAULT FALSE,
    avif_autodetection BOOLEAN DEFAULT FALSE,
    file_size_limit BIGINT,
    allowed_mime_types TEXT[]
);

-- objects table (documented for reference)
-- Note: Usually auto-created by Supabase Storage
CREATE TABLE IF NOT EXISTS objects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bucket_id TEXT REFERENCES buckets(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    owner UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    path_tokens TEXT[] GENERATED ALWAYS AS (string_to_array(name, '/')) STORED,
    version TEXT,
    owner_id TEXT,
    UNIQUE(bucket_id, name)
);

COMMENT ON TABLE buckets IS 'Supabase Storage buckets (system table)';
COMMENT ON TABLE objects IS 'Supabase Storage objects/files (system table)';
