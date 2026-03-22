# SQL migrations (manual / DBA)

Ordered, hand-written SQL for production-style upgrades. Use when you need explicit review or changes outside Alembic.

## Order

| File | Purpose |
|------|---------|
| [supabase_auth_patch.sql](supabase_auth_patch.sql) | **Legacy** — drops `password_hash`, adds `supabase_uid` for DBs that still had local passwords. Skip if you already use `db/schema.sql` v3.3+ for greenfield installs. |
| [002_users_supabase_roles_v33.sql](002_users_supabase_roles_v33.sql) | Expands `users.role` CHECK and finishes `users` shape for v3.3 (requires every user row to have `supabase_uid` set). |
| [003_employees_employment_full_time.sql](003_employees_employment_full_time.sql) | Extends `employees.employment_type` CHECK to include `full_time`. |

## Relationship to Alembic

- **Greenfield:** Prefer loading [../schema.sql](../schema.sql), then `alembic stamp head` so Alembic revision matches reality (see [../README.md](../README.md)).
- **Existing DB:** Apply the numbered `.sql` files here in order, backfill data as documented in each file, then align Alembic history with `alembic stamp <revision>`.

## Applying

```bash
psql "$DATABASE_URL" -f db/migrations/002_users_supabase_roles_v33.sql
```

Always test on a copy first.
