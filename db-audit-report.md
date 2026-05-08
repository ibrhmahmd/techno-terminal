# Database Schema Audit Report

**Techno Future Academy — Management System**
_May 2026_

---

## 1. Executive Summary

This report covers a full audit of the `techno-future-auth` Supabase project (PostgreSQL 17, region: eu-north-1). The schema powers a growing coding academy managing students, groups, courses, sessions, attendance, payments, and competition tracking.

The overall design is well-structured for its current scale. The team has clearly applied good practices such as RLS on all tables, consistent use of soft deletes, a normalized financial model, and thoughtful indexing. However, several technical debts have been identified that will create real problems on the path to 5,000 students if not addressed.

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 2 |
| 🟠 HIGH | 4 |
| 🟡 MEDIUM | 5 |
| 🟢 LOW / INFO | 4 |

---

## 2. Schema Overview

The schema contains **20 tables**, **14 views**, **3 trigger functions**, and **12 custom triggers**. All tables have RLS enabled. The domain model breaks into 5 logical modules:

| Module | Tables | Purpose |
|--------|--------|---------|
| People | `students`, `parents`, `student_parents`, `employees`, `users` | Core identity: students with optional parent linkage, employee/user auth bridge |
| Academic | `courses`, `groups`, `group_levels`, `group_course_history`, `sessions` | Course catalog → groups → per-level tracking → scheduled sessions |
| Enrollment | `enrollments`, `enrollment_level_history`, `attendance` | Student-to-group binding, level progression, per-session attendance |
| Finance | `payments`, `receipts` | Immutable ledger (charge/payment/refund) with receipt aggregation |
| Competitions | `competitions`, `teams`, `team_members`, `group_competition_participation` | Annual competitions, student team membership, group participation tracking |

---

## 3. Findings — Full Registry

| ID | Severity | Table(s) | Issue | Impact | Recommendation |
|----|----------|----------|-------|--------|----------------|
| F-01 | 🔴 CRITICAL | `teams` | Triple soft-delete: `is_deleted` (bool), `deleted_at` (timestamp), AND `deleted_by` + `deleted_by_user_id` (two actor columns). Three mechanisms for one concept. | Data integrity risk — they can diverge silently. `active_teams` view only checks `deleted_at`, ignoring `is_deleted`. | Deprecate `is_deleted`. Standardize on `deleted_at` + `deleted_by`. Drop `deleted_by_user_id` or merge into one column via migration. |
| F-02 | 🔴 CRITICAL | `student_activity_log` | Two JSONB columns: `metadata` and `meta` — both indexed with GIN. One is clearly a deprecated remnant from migration 043. | Double storage cost, double GIN index maintenance. Queries must know which column to read. | Identify which column is active (likely `meta` from latest migrations). Migrate data, drop the unused column and its GIN index. |
| F-03 | 🟠 HIGH | `sessions`, `enrollments`, `groups` | `level_number` is stored redundantly in 3 places: `groups.level_number`, `sessions.level_number`, `enrollments.level_number` — each separate from the `group_levels` FK. | Any of the three can drift out of sync. No DB constraint enforces consistency. | Make `group_levels` the single source of truth. Derive `level_number` from `group_level_id` via FK lookups in queries/views rather than storing it. |
| F-04 | 🟠 HIGH | `v_enrollment_balance`, `v_unpaid_enrollments` | `v_enrollment_balance` is a non-materialized aggregating view. `v_unpaid_enrollments` then joins it. At 5,000 students this double-view chain recalculates every payment on every page load. | Severe performance degradation under load. The financial dashboard will become the system bottleneck. | Materialize `v_enrollment_balance` with REFRESH on payment INSERT/UPDATE/DELETE triggers. Or cache balance on `enrollments` table with a trigger-maintained balance column. |
| F-05 | 🟠 HIGH | `users` | Two identical unique indexes on `supabase_uid`: `idx_users_supabase_uid` and `users_supabase_uid_key`. Both are UNIQUE BTREE on the same column. | Wasted storage and write overhead — every INSERT/UPDATE updates two identical indexes. | Drop one: `DROP INDEX idx_users_supabase_uid;` (keep the constraint-generated `users_supabase_uid_key`). |
| F-06 | 🟠 HIGH | `notification_logs` | `recipient_id` is a polymorphic foreign key (PARENT, EMPLOYEE, ADDITIONAL) with no referential integrity — just a plain integer. | No DB-level guarantee that referenced recipients exist. Silent orphans on parent/employee deletion. | Either split into separate nullable FKs (`parent_id`, `employee_id`), or add a CHECK or trigger to validate existence. |
| F-07 | 🟡 MEDIUM | `v_enrollment_attendance` | The view filters for `status IN ('present', 'late')` but `attendance.status` has a CHECK constraint that only allows `'present'`, `'absent'`, `'cancelled'`. The `'late'` status can never exist. | Dead filter clause; misleading to developers reading the view. | Remove `'late'` from the view filter, or add `'late'` to the attendance status CHECK constraint if it is a future requirement. |
| F-08 | 🟡 MEDIUM | `v_daily_collections` | Hard-coded 30-day WHERE filter: `CURRENT_DATE - '30 days'`. The view is not reusable for historical reporting. | Cannot query revenue by month, quarter, or custom date ranges without rewriting the view. | Remove the date filter from the view. Let the application layer or a wrapper query pass the date range. |
| F-09 | 🟡 MEDIUM | `admin_notification_settings`, `notification_additional_recipients`, `notification_templates` | Three tables have `updated_at` columns but no trigger to auto-update them on row changes. | `updated_at` will always show the insert timestamp — change tracking is silently broken. | Add `tf_set_updated_at` triggers to all three tables, consistent with the rest of the schema. |
| F-10 | 🟡 MEDIUM | `students` | Full-text search index is a plain BTREE on `full_name`. BTREE only supports prefix search (`LIKE 'name%'`). Searching by partial name (`LIKE '%name%'`) does a full table scan. | At 5,000 students, name search in the UI will be slow and unusable. | Add a GIN index with pg_trgm: `CREATE EXTENSION pg_trgm; CREATE INDEX idx_students_name_trgm ON students USING GIN (full_name gin_trgm_ops);` |
| F-11 | 🟡 MEDIUM | `teams` | `category_id` column still exists with an index (`idx_teams_category`) even though the schema comment explicitly states `competition_id` replaces it. | Deprecated column creates confusion and maintains a dead index. | Confirm `category_id` is unused in application code, then `DROP COLUMN category_id` and `DROP INDEX idx_teams_category`. |
| F-12 | 🟢 LOW | `sessions` | No index on `(session_date, group_id)` composite. Schedule queries that filter by date range and group will hit separate indexes at best. | Sub-optimal scheduling queries. Will degrade as sessions grow. | `CREATE INDEX idx_sessions_date_group ON sessions (session_date, group_id);` |
| F-13 | 🟢 LOW | `sessions` | No index on `actual_instructor_id` despite it being a FK to `employees` and a likely filter for instructor schedule views. | Instructor schedule queries do a full sessions scan. | `CREATE INDEX idx_sessions_instructor ON sessions (actual_instructor_id);` |
| F-14 | 🟢 LOW | `group_course_history` | Purpose overlaps with `groups.course_id`. It seems to track course reassignments over time, but this is not documented and the relationship to `group_levels.course_id` is unclear. | Developer confusion, risk of the history falling out of sync. | Add a table comment clarifying the purpose and the expected write path. Clarify if `group_levels.course_id` is always identical to `groups.course_id`. |
| F-15 | 🟢 INFO | `payments` | `payments.student_id` is redundant — `student_id` is already derivable via `payments → enrollments → students`. | Minor redundancy and write overhead maintaining the denormalization. | Acceptable trade-off for direct payment-to-student queries, but document it explicitly as an intentional denormalization. |

---

## 4. Detailed Analysis by Module

### 4.1 People Module

#### `students`

Strong design. Soft delete pattern is correctly implemented with `deleted_at` + `deleted_by`, and `active_students` / `deleted_students` views provide clean consumer interfaces. The waiting list implementation (`waiting_since`, `waiting_priority`, `waiting_notes`) is pragmatic.

> ⚠️ **F-10** — BTREE index on `full_name` only supports prefix search. Add `pg_trgm` GIN index for partial name lookup before user load grows.

#### `users / employees`

The `users ↔ employees` 1:1 bridge via `user_id` / `employee_id` is sound for the Supabase auth integration. Role enum (`admin`, `instructor`, `system_admin`) is appropriate for current scope.

> ⚠️ **F-05** — Duplicate unique index on `supabase_uid` wastes write performance. Drop `idx_users_supabase_uid` immediately — it's a one-line fix.

#### `parents / student_parents`

The many-to-many `student_parents` junction with `is_primary` flag is clean. The `parents` table is currently empty (0 rows) — ensure the application is populating it correctly if parent contact management is a live feature.

---

### 4.2 Academic Module

#### `courses → groups → group_levels`

This three-tier hierarchy is the core of the academic model and is generally well designed. Courses define the catalog; groups are scheduled class cohorts; `group_levels` tracks per-cohort level progression with pricing overrides and instructor assignments.

> 🔴 **F-03** — `level_number` is denormalized into `groups`, `sessions`, AND `enrollments` independently. The `group_levels` table is the authoritative source but nothing enforces the three copies stay in sync. This is a data integrity time bomb.

#### `sessions`

Sessions correctly link to both `group_id` and `group_level_id`, and track substitute instructors with `is_substitute`. The `is_extra_session` flag is a clean way to distinguish make-up sessions from regular ones.

> ⚠️ **F-12 + F-13** — Missing composite index on `(session_date, group_id)` and missing index on `actual_instructor_id`. Both are cheap to add and will matter for schedule queries.

---

### 4.3 Enrollment & Attendance Module

#### `enrollments`

The partial unique index `idx_enrollments_active_unique` (`student_id`, `group_id` WHERE `status='active'`) correctly prevents duplicate active enrollments. The status enum (`active`, `completed`, `transferred`, `dropped`) covers the full lifecycle well.

#### `attendance`

Attendance correctly references both `session_id` and `enrollment_id` for full query flexibility. The `student_id` denormalization on `attendance` is acceptable for performance.

> ⚠️ **F-07** — `v_enrollment_attendance` filters for `'late'` status which cannot exist per the attendance CHECK constraint. This is dead code.

---

### 4.4 Finance Module

#### `payments / receipts`

The financial model is a well-designed immutable ledger. Using `transaction_type` (`charge`, `payment`, `refund`) rather than mutable balances is the correct pattern for financial integrity. The `v_enrollment_balance` view computes balance dynamically from the ledger — correct in principle.

> 🔴 **F-04** — `v_enrollment_balance` is non-materialized and `v_unpaid_enrollments` chains on top of it. At scale, every balance check re-aggregates all payment rows for every enrollment. This **will** cause performance collapse.

**Recommended materialization strategy:**

1. `CREATE MATERIALIZED VIEW mv_enrollment_balance AS (SELECT ... FROM v_enrollment_balance)`
2. Add trigger function on `payments` INSERT/UPDATE/DELETE to call `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_enrollment_balance`
3. Alternatively, maintain a cached `balance` column on `enrollments` updated by triggers — simpler and faster for point lookups

---

### 4.5 Competitions Module

#### `teams`

The competition tracking model supports teams per competition with `category`/`subcategory` using `citext` for case-insensitive matching — a thoughtful choice. Placement tracking (`placement_rank`, `placement_label`) is clean.

> 🔴 **F-01** — The `teams` table has three overlapping soft-delete mechanisms: `is_deleted` (boolean), `deleted_at` (timestamp), `deleted_by` (integer), and `deleted_by_user_id` (integer). The `active_teams` view only checks `deleted_at` — meaning a row could have `is_deleted=true` but still appear in `active_teams`.

> ⚠️ **F-11** — `category_id` column is documented as replaced by `competition_id` but still exists with an active index. Dead column.

---

## 5. Deprecated Logic to Clean Up

| Item | Location | Action |
|------|----------|--------|
| `meta` JSONB column | `student_activity_log` | Identify active column (`meta` vs `metadata`), migrate if needed, DROP the unused one + its GIN index |
| `is_deleted` boolean | `teams` | Remove column after confirming all queries use `deleted_at`. Update `active_teams` view. |
| `deleted_by_user_id` column | `teams` | Merge into `deleted_by` or drop — both reference `users.id` for the same concept |
| `category_id` column + index | `teams` | Confirm unused in app code, then `DROP COLUMN` + `DROP INDEX idx_teams_category` |
| `idx_users_supabase_uid` index | `users` | `DROP INDEX` — exact duplicate of the constraint-generated unique index |
| `'late'` in `v_enrollment_attendance` | view | Remove from filter or add to `attendance` CHECK constraint |
| 30-day hardcode in `v_daily_collections` | view | Remove WHERE clause, push date filtering to application layer |

---

## 6. Performance & Scalability Assessment

### 6.1 What's Working Well

- **Partial indexes on hot paths** (`active enrollments`, `active groups`, `waiting students`) are well-targeted.
- **GIN indexes on JSONB columns** in `student_activity_log` support flexible metadata queries.
- **Composite index** `idx_enrollments_group_level_active` covers the most common enrollment list query.
- **Soft-delete with partial index** on `deleted_at` avoids polluting live queries.
- **`citext`** on `teams.category`/`subcategory` eliminates application-layer case normalization.

### 6.2 Scalability Risks at 5,000 Students

- 🔴 **View chaining (F-04):** `v_unpaid_enrollments → v_enrollment_balance` will be the #1 bottleneck. Address before reaching 1,000 enrollments.
- 🔴 **Full-table name search (F-10):** `LIKE '%name%'` on `students.full_name` scans all rows. Add trigram GIN index before any marketing push.
- ⚠️ **Sessions table growth:** Without `(session_date, group_id)` composite index, schedule grid views will degrade linearly.
- ⚠️ **`notification_logs`:** No retention policy — this table will grow unboundedly with every notification sent. Add a cron job or `pg_partman` time-based partitioning if notification volume is high.
- ⚠️ **`student_activity_log`:** Same unbounded growth concern. Consider archiving rows older than 2 years to a separate table.

---

## 7. Security & RLS Observations

All 20 tables have RLS enabled — a strong baseline. However:

- The `users` table role enum (`admin`, `instructor`, `system_admin`) should be the foundation of all RLS policies. Confirm that instructor-role users cannot read payment or salary data.
- The `employees` table stores `monthly_salary` and `contract_percentage` — ensure RLS policies restrict these to `admin`/`system_admin` roles only.
- `notification_logs.recipient_id` is unvalidated at the DB level (F-06). If RLS policies rely on `recipient_id` for row-level filtering, this is a security gap.
- The `parents` table has 0 rows currently. If a parent portal is planned, `student_parents` will need corresponding RLS policies before launch.

---

## 8. Design Strengths

- **Immutable financial ledger.** Using `transaction_type` rows (charge/payment/refund) rather than mutable balance fields is the correct pattern for financial data integrity.
- **Consistent soft-delete pattern.** `students`, `payments`, `competitions`, and `teams` all implement soft deletes with paired views (`active_*` / `deleted_*`). The `teams` table is the only exception.
- **Trigger-managed `updated_at`.** The `tf_set_updated_at` function is consistently applied across 9 tables with no exceptions in the core domain tables.
- **Partial unique index for active enrollments.** `idx_enrollments_active_unique` prevents duplicate active enrollments at the DB level — no application-layer check needed.
- **`citext` for competition categories.** Case-insensitive matching on `teams.category` avoids `'Robotics'` vs `'robotics'` mismatches.
- **`student_activity_log` consolidation.** Migration 043 correctly merged 3 separate history tables into a single unified timeline — clean and extensible.
- **Waiting list implementation.** `waiting_since`, `waiting_priority`, and `waiting_notes` on `students` is a practical, low-overhead implementation that avoids a separate table.

---

## 9. Recommended Action Plan

### Immediate (before next release)

- **F-05:** Drop duplicate `supabase_uid` index — 1 line, zero risk
- **F-07:** Fix `v_enrollment_attendance` `'late'` filter inconsistency
- **F-09:** Add `updated_at` triggers to 3 notification tables

### Short-term (next sprint)

- **F-01:** Unify `teams` soft-delete — consolidate `is_deleted` + `deleted_by_user_id`
- **F-02:** Identify and drop the unused JSONB column in `student_activity_log`
- **F-10:** Add `pg_trgm` GIN index on `students.full_name`
- **F-11:** Drop `teams.category_id` and its dead index
- **F-08:** Remove hardcoded 30-day filter from `v_daily_collections`

### Medium-term (before scaling past ~1,000 students)

- **F-04:** Materialize `v_enrollment_balance` — this is the highest-impact single change
- **F-03:** Audit and enforce `level_number` consistency across `groups`/`sessions`/`enrollments`
- **F-12 + F-13:** Add missing session indexes
- **F-06:** Add recipient validation to `notification_logs`
- **F-14:** Document `group_course_history` write path and relationship to `group_levels`

---

_End of Report — Generated May 2026_
