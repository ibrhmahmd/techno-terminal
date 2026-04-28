# Database Layout (Hybrid: SQL + Alembic)

## Contents

- **[schema/](schema/)** — **Modular PostgreSQL DDL (v4.0)**. Source of truth organized by domain:
  - `00-10` — Tables organized by domain (core, crm, academics, etc.)
  - `20-60` — Database objects (indexes, views, functions, triggers, constraints)
  - `90` — Seed data
- **[schema.sql](schema.sql)** — **Orchestrator** that includes all modular files. Use for creating a new environment with `psql`.
- **[migrations/](migrations/)** — Hand-written SQL for upgrading **existing** databases (CHECK changes, auth columns, DBA-reviewed scripts).
- **Alembic** (repo root: `alembic.ini`, `alembic/`) — Revision history for evolving the schema from Python; use when the team prefers autogenerate/migrate workflows.

## Schema Overview

| Metric | Count |
|--------|-------|
| Tables | 33 |
| Views | 15 |
| Indexes | 94 |
| Triggers | 17 |
| Functions | 6 |

## Schema Files Organization

| File | Contents | Description |
|------|----------|-------------|
| `schema/00_extensions.sql` | PostgreSQL extensions | Required extensions (uuid-ossp, pgcrypto, citext) |
| `schema/01_enums.sql` | Custom ENUM types | student_status and other custom types |
| `schema/02_tables_core.sql` | Core tables | parents, employees, users |
| `schema/03_tables_crm.sql` | CRM tables | students, student_parents, student_activity_log |
| `schema/04_tables_academics.sql` | Academic tables | courses, groups, sessions, group_levels, group_course_history |
| `schema/05_tables_enrollments.sql` | Enrollment tables | enrollments, enrollment_level_history, attendance |
| `schema/06_tables_finance.sql` | Finance tables | receipts, payments, receipt_templates |
| `schema/07_tables_competitions.sql` | Competition tables | competitions, competition_categories, teams, team_members, group_competition_participation |
| `schema/08_tables_notifications.sql` | Notification tables | notification_templates, notification_logs, notification_subscribers, notification_additional_recipients, admin_notification_settings |
| `schema/09_tables_history.sql` | History tables | Reserved for future audit tables |
| `schema/10_tables_supabase.sql` | Supabase tables | subscription, hooks, buckets, objects |
| `schema/20_indexes.sql` | All indexes | 94 indexes organized by table |
| `schema/30_views.sql` | All views | 15 views including soft-delete filters and analytics |
| `schema/40_functions.sql` | Custom functions | Trigger functions and utility functions |
| `schema/50_triggers.sql` | All triggers | 17 triggers for audit and business logic |
| `schema/60_constraints.sql` | Additional constraints | Complex constraints (mostly reserved) |
| `schema/90_seed_data.sql` | Seed data | Initial data for templates, categories, admin employee |

## Environment variables

- `DATABASE_URL` — PostgreSQL connection string.
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — app + API JWT validation.
- `SUPABASE_SERVICE_ROLE_KEY` — staff provisioning, password reset, `app/db/seed.py` (optional for read-only dev).

## Bootstrap paths

### A. New database (SQL-first)

1. `psql "$DATABASE_URL" -f db/schema.sql`
2. Run the app once with `python run_ui.py` (or `python -m app.db.seed`) to map the admin user in Supabase to `users.supabase_uid`.
3. `alembic stamp head` so Alembic matches the baseline (no DDL run by Alembic if revisions are empty/pass-only).

### B. Existing database (upgrade)

1. Read [migrations/README.md](migrations/README.md) and apply required `.sql` files in order.
2. Backfill `users.supabase_uid` for every row before constraints enforce `NOT NULL`.
3. Stamp or upgrade Alembic per team convention (documented in `alembic/README.md` if present).

## Migrating local PostgreSQL → Supabase (one schema file + all data)

### Single file for schema (DDL)

Use **[schema.sql](schema.sql)** as the **only** file needed to recreate tables, indexes, views, triggers, and functions in a **new** empty database. It is kept in sync with numbered migrations under `migrations/`; you do **not** need to run those files on a greenfield Supabase DB if `schema.sql` is current.

### Before you start

1. Install **PostgreSQL client tools** on your machine (`psql`, `pg_dump`, `pg_restore`). On Windows, use the [PostgreSQL EDB installer](https://www.postgresql.org/download/windows/) or `choco install postgresql`.
2. In Supabase: **Project Settings → Database** — copy the **URI** (use **Session pooler** if your network needs IPv4; use **Direct** for `pg_restore` if the pooler rejects it). Append `?sslmode=require` if not present.
3. **Auth vs `public.users`:** This app maps **Supabase Auth** (`auth.users`) to **`public.users`** via **`users.supabase_uid`**. Rows you copy into `public.users` must use UUIDs that **exist in Supabase Auth** for those people to log in. After moving data, either create Auth users first, then load `public.users` with matching `supabase_uid`, or load data and then create/link accounts and **update** `public.users.supabase_uid`.

### Path A — Recommended: schema first, then data only

**1. Create the empty schema on Supabase**

```bash
psql "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require" -f db/schema.sql
```

(Use your real URI; port **5432** with the **direct** host `db.[PROJECT_REF].supabase.co` is fine if you prefer.)

**2. Export only the data from your local database**

```bash
set PGPASSWORD=your_local_password
pg_dump "postgresql://USER@localhost:5432/LOCAL_DBNAME" --data-only --format=custom --no-owner --no-acl -f techno_data.dump
```

**3. Import the data into Supabase**

```bash
set PGPASSWORD=your_supabase_password
pg_restore -d "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require" --data-only --no-owner --no-acl --single-transaction techno_data.dump
```

If the pooler rejects `pg_restore`, switch the target URI to the **direct** connection (port **5432**).

**4. Fix sequences if needed**

```sql
SELECT setval(pg_get_serial_sequence('parents', 'id'), (SELECT MAX(id) FROM parents));
-- repeat for other tables as needed
```

**5. Point the app at Supabase**

Set **`DATABASE_URL`** in `.env` to the connection string the app should use (often the **pooler** for many concurrent connections).

### Path B — One-shot full dump (empty target `public` only)

If the Supabase database has **no** conflicting objects in `public`:

```bash
pg_dump "postgresql://USER@localhost:5432/LOCAL_DB" --format=custom --no-owner --no-acl -f full.dump
pg_restore -d "postgresql://...@...supabase...?sslmode=require" --no-owner --no-acl full.dump
```

Avoid this if Supabase already has `schema.sql` applied — use Path A instead.

### What not to migrate

- Do **not** manually replace Supabase’s **`auth`** schema; manage login users via Supabase Auth + **`public.users`**.
- Do **not** run `db/migrations/supabase_auth_patch.sql` on a DB that already matches **`db/schema.sql`** v3.3 (legacy upgrades only).

## Adding a new `users.role`

1. Add the value to `app/modules/auth/role_types.py` (`UserRole` + `ALL_ROLE_VALUES`).
2. Update `CHECK (role IN (...))` in `db/schema/02_tables_core.sql` and add a new numbered file under `db/migrations/`.
3. Add an Alembic revision if you use Alembic to alter constraints in deployed environments.

## Schema Patterns

### Soft Delete
Tables with soft delete support include `deleted_at` and `deleted_by` columns:
- `students`
- `payments`
- `enrollments`
- `competitions`
- `teams`

Use `active_*` views (e.g., `active_students`) to filter out deleted records.

### Status Tracking
- `students.status` — ENUM: active, waiting, inactive
- `students.status_history` — JSONB array tracking all status changes
- `enrollments.status` — active, completed, transferred, dropped
- `groups.status` — active, inactive, completed, archived

### Audit Timestamps
All tables have:
- `created_at` — Set on INSERT (DEFAULT CURRENT_TIMESTAMP)
- `updated_at` — Auto-updated via trigger on UPDATE

Triggers are defined in `schema/50_triggers.sql` and use `tf_set_updated_at()` function.

## Maintenance Guidelines

### Adding a New Table

1. Determine the appropriate domain file (e.g., academics → `04_tables_academics.sql`)
2. Add the CREATE TABLE statement with:
   - Primary key (SERIAL or UUID)
   - Foreign key references with appropriate ON DELETE actions
   - `created_at` and `updated_at` timestamps
   - `metadata` JSONB for extensibility
3. Add relevant indexes to `20_indexes.sql`
4. Add updated_at trigger to `50_triggers.sql` if needed
5. Update this README with the table name

### Adding a New View

1. Add to `schema/30_views.sql`
2. Use `CREATE OR REPLACE VIEW` for idempotency
3. Add a COMMENT ON VIEW statement
4. Document any dependencies or soft-delete filtering

### Modifying an Existing Table

For existing databases, **always create a migration** in `db/migrations/`:
```sql
-- Migration XXX: Add column to table
ALTER TABLE table_name ADD COLUMN new_column TYPE;
```

For new environments, update the appropriate `schema/*.sql` file.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v4.0 | 2026-04-28 | Modular schema refactor — split monolithic schema.sql into domain-organized files |
| v3.3 | 2025-XX-XX | Supabase auth integration, users table with supabase_uid |
| v3.2 | 2025-XX-XX | ON DELETE CASCADE → RESTRICT changes for data integrity |
| v3.1 | 2025-XX-XX | Initial soft-delete pattern implementation |
