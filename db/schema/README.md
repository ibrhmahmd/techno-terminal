# Modular Database Schema

This directory contains the modular PostgreSQL schema for the Techno Terminal CRM system.

## File Naming Convention

Files are numbered to indicate loading order:

| Range | Purpose |
|-------|---------|
| `00-01` | Infrastructure (extensions, enums) |
| `02-10` | Tables organized by domain |
| `20` | Indexes |
| `30` | Views |
| `40` | Functions |
| `50` | Triggers |
| `60` | Additional constraints |
| `90` | Seed data |

## Dependency Order

When adding new files or modifying existing ones, maintain this dependency order:

```
00_extensions.sql
01_enums.sql
02_tables_core.sql (parents, employees, users — no dependencies)
03_tables_crm.sql (students — depends on parents, users)
04_tables_academics.sql (courses, groups — depends on employees)
05_tables_enrollments.sql (enrollments — depends on students, groups)
06_tables_finance.sql (payments — depends on students, enrollments, receipts)
07_tables_competitions.sql (competitions — depends on groups, students, employees)
08_tables_notifications.sql (notifications — depends on users)
09_tables_history.sql (history tables — depends on various)
10_tables_supabase.sql (Supabase tables)
20_indexes.sql (all tables must exist first)
30_views.sql (depends on tables)
40_functions.sql (standalone)
50_triggers.sql (depends on tables and functions)
60_constraints.sql (depends on tables)
90_seed_data.sql (depends on all tables)
```

## Using the Schema

### Apply Complete Schema

```bash
psql "$DATABASE_URL" -f db/schema.sql
```

### Apply Individual Modules

```bash
# Core tables only
psql "$DATABASE_URL" -f db/schema/02_tables_core.sql

# Add CRM tables
psql "$DATABASE_URL" -f db/schema/03_tables_crm.sql
```

### Development: Reset and Recreate

```bash
# WARNING: This drops all data!
psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql "$DATABASE_URL" -f db/schema.sql
```

## Idempotency

All schema files are designed to be idempotent (safe to run multiple times):

- `DROP IF EXISTS` before `CREATE`
- `CREATE OR REPLACE` for views and functions
- `IF NOT EXISTS` for indexes

## Adding New Objects

### New Table

1. Choose appropriate domain file (or create new if needed)
2. Add `DROP TABLE IF EXISTS ... CASCADE` at top of file
3. Add `CREATE TABLE` with:
   - Primary key
   - Foreign keys with `ON DELETE` actions
   - `created_at` and `updated_at` TIMESTAMPTZ
   - `metadata` JSONB DEFAULT '{}'
4. Add `COMMENT ON TABLE` and `COMMENT ON COLUMN` statements
5. Add indexes to `20_indexes.sql`
6. Add trigger to `50_triggers.sql` for `updated_at`

### New Column to Existing Table

**For new environments:**
1. Add to appropriate `schema/*.sql` file

**For existing databases:**
1. Create migration in `db/migrations/`
2. Migration naming: `XXX_description.sql`

### New View

1. Add to `30_views.sql`
2. Use `CREATE OR REPLACE VIEW`
3. Include soft-delete filtering where applicable
4. Add `COMMENT ON VIEW`

## Schema Validation

After applying schema, verify counts:

```sql
-- Tables
SELECT count(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
-- Expected: 33

-- Views
SELECT count(*) FROM pg_views WHERE schemaname = 'public';
-- Expected: 15

-- Indexes
SELECT count(*) FROM pg_indexes WHERE schemaname = 'public';
-- Expected: 94

-- Triggers
SELECT count(*) FROM pg_trigger 
WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace = 'public'::regnamespace);
-- Expected: 17+
```

## Troubleshooting

### "relation does not exist" error

Check that files are being loaded in correct order. Tables must be created before views/indexes that reference them.

### "cannot drop table ... because other objects depend on it"

Use `DROP TABLE ... CASCADE` to automatically drop dependent objects.

### View dependency errors

Views in `30_views.sql` reference tables. Ensure all table files are loaded first.

## Schema Documentation

Tables and columns should have comments explaining their purpose:

```sql
COMMENT ON TABLE table_name IS 'Description of table purpose';
COMMENT ON COLUMN table_name.column_name IS 'Description of column';
```

These comments appear in database IDEs and documentation generators.
