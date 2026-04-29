-- =============================================================================
-- Techno Terminal — PostgreSQL Schema v4.0
-- Modular Schema Orchestrator
-- 33 tables, 15 views, 94 indexes, 17 triggers, 6 functions
-- Last Updated: 2026-04-28
-- =============================================================================
--
-- This file serves as the orchestrator for the modular schema.
-- It includes all schema files in the correct dependency order.
--
-- To apply the complete schema:
--   psql "$DATABASE_URL" -f db/schema.sql
--
-- To apply individual modules:
--   psql "$DATABASE_URL" -f db/schema/02_tables_core.sql
--
-- Schema Organization:
--   00_extensions.sql      - PostgreSQL extensions
--   01_enums.sql         - Custom ENUM types
--   02_tables_core.sql    - parents, employees, users
--   03_tables_crm.sql    - students, student_parents, activity_log
--   04_tables_academics.sql - courses, groups, sessions, group_levels
--   05_tables_enrollments.sql - enrollments, attendance, level_history
--   06_tables_finance.sql - receipts, payments, templates
--   07_tables_competitions.sql - competitions, teams, members
--   08_tables_notifications.sql - notification system tables
--   09_tables_history.sql - audit and history tables
--   10_tables_supabase.sql - Supabase system tables
--   20_indexes.sql        - All indexes
--   30_views.sql          - All views
--   40_functions.sql      - Custom functions
--   50_triggers.sql       - All triggers
--   60_constraints.sql    - Additional constraints
--   90_seed_data.sql      - Initial seed data
--
-- =============================================================================
-- Stop on any error
\set ON_ERROR_STOP on

-- =============================================================================
-- INCLUDE ALL SCHEMA MODULES
-- =============================================================================

-- Core infrastructure
\i schema/00_extensions.sql
\i schema/01_enums.sql

-- Tables (in dependency order)
\i schema/02_tables_core.sql
\i schema/03_tables_crm.sql
\i schema/04_tables_academics.sql
\i schema/05_tables_enrollments.sql
\i schema/06_tables_finance.sql
\i schema/07_tables_competitions.sql
\i schema/08_tables_notifications.sql
\i schema/09_tables_history.sql
\i schema/10_tables_supabase.sql

-- Database objects
\i schema/20_indexes.sql
\i schema/30_views.sql
\i schema/40_functions.sql
\i schema/50_triggers.sql
\i schema/60_constraints.sql
\i schema/90_seed_data.sql

-- =============================================================================
-- SCHEMA VERIFICATION
-- =============================================================================

COMMENT ON SCHEMA public IS 'Techno Terminal CRM Database Schema v4.0 — 33 tables, 15 views, 94 indexes, 17 triggers. Modular schema last updated 2026-04-28.';

-- Verify schema version
SELECT 'Techno Terminal Schema v4.0 applied successfully' AS status,
       (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE') AS table_count,
       (SELECT count(*) FROM pg_views WHERE schemaname = 'public') AS view_count,
       (SELECT count(*) FROM pg_indexes WHERE schemaname = 'public') AS index_count;