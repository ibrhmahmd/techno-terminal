-- =============================================================================
-- EXTENSIONS
-- PostgreSQL extensions required by the Techno Terminal database
-- =============================================================================

-- UUID generation support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptographic functions (for password hashing, etc.)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Case-insensitive text support
CREATE EXTENSION IF NOT EXISTS "citext";
