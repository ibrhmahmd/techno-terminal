# SQL migrations (manual / DBA)

Ordered, hand-written SQL for production-style upgrades. Use when you need explicit review or changes outside Alembic.

## Order

| File | Purpose |
|------|---------|
| [supabase_auth_patch.sql](supabase_auth_patch.sql) | **Legacy** — drops `password_hash`, adds `supabase_uid` for DBs that still had local passwords. Skip if you already use `db/schema.sql` v3.3+ for greenfield installs. |
| [002_users_supabase_roles_v33.sql](002_users_supabase_roles_v33.sql) | Expands `users.role` CHECK and finishes `users` shape for v3.3 (requires every user row to have `supabase_uid` set). |
| [003_employees_employment_full_time.sql](003_employees_employment_full_time.sql) | Extends `employees.employment_type` CHECK to include `full_time`. |
| [004_employees_sprint2_identity.sql](004_employees_sprint2_identity.sql) | Sprint 2: `national_id`, education columns, `employment_type` NOT NULL, phone/email/national_id uniqueness, D5 contract-% CHECK. |
| [005_audit_d4_timestamps.sql](005_audit_d4_timestamps.sql) | Sprint 3 (D4): backfill NULL audit timestamps, `DEFAULT CURRENT_TIMESTAMP`, `tf_set_updated_at` triggers on core tables. |
| [006_receipts_paid_at_index.sql](006_receipts_paid_at_index.sql) | Sprint 4 (B9): `idx_receipts_paid_at` for receipt discovery by `paid_at` range. |
| [007_p6_enrollment_balance.sql](007_p6_enrollment_balance.sql) | Sprint 6 (B8 / P6): `v_enrollment_balance.balance` = `total_paid - net_due` (negative = debt). |
| [008_rename_guardians_to_parents.sql](008_rename_guardians_to_parents.sql) | Renames the `guardians` table and all FK references to `parents`. |
| [008_v_course_stats.sql](008_v_course_stats.sql) | Adds the `v_course_stats` analytics view. |
| [009_core_logic_refactor.sql](009_core_logic_refactor.sql) | Core logic refactor — schema cleanups aligned with the service-layer refactor. |
| [010_phase2_competition_fees.sql](010_phase2_competition_fees.sql) | **Phase 2:** Adds `competitions.fee_per_student` and `team_members.member_share` (snapshotted at registration). Backfills `member_share` from the legacy `teams.enrollment_fee_per_student` column. |

## Relationship to Alembic

- **Greenfield:** Prefer loading [../schema.sql](../schema.sql), then `alembic stamp head` so Alembic revision matches reality (see [../README.md](../README.md)).
- **Existing DB:** Apply the numbered `.sql` files here in order, backfill data as documented in each file, then align Alembic history with `alembic stamp <revision>`.

## Applying

```bash
psql "$DATABASE_URL" -f db/migrations/010_phase2_competition_fees.sql
```

Always test on a copy first.

If a statement fails inside a script wrapped in `BEGIN` … `COMMIT` (e.g. `005_audit_d4_timestamps.sql`), PostgreSQL enters an **aborted transaction**; further commands return **SQLSTATE 25P02** until you run **`ROLLBACK;`** (or use a new connection), then re-apply the **whole** script from the start.

