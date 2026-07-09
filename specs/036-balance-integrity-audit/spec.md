# Spec 036 — Student Balance Integrity Audit

**Status:** FINALIZED  
**Date:** 2026-07-09  
**Supabase Project:** `techno-future-auth` (`srbppkcvrgioneitktdj`)  
**Relates to:** `specs/035-business-reports-feature/spec.md`

---

## Decisions Log

| # | Question | Decision |
|---|----------|----------|
| 1 | Report-blocking on Scenario G | Emit `data_quality_warning` and continue — do not block |
| 2 | Severity tiers | ✅ Yes — ERROR / WARNING / INFO tiers per scenario |
| 3 | Visualization path | **Postgres views + Supabase SQL Editor** — fastest, zero dev overhead |
| 4 | UI access | Backend/DB only for now — data is the priority |
| 5 | Automated alerts | Not yet |
| 6 | `start_date` filter | ✅ Yes — add optional `enrolled_after` / `paid_after` param to exclude migration artifacts |

---

## 1. Problem Statement

The Techno Terminal database has 678 enrollments and 387 payment records spanning ~2 months of live operations. With data at a scale where manual review is no longer feasible, there is a need to **systematically detect and surface suspicious or inconsistent financial and enrollment records** before they distort reports, invoices, and business decisions.

---

## 2. Visualization Strategy (Question 3 Answer)

**Chosen approach: Postgres views installed via migration `074_audit_views.sql`**

Why this is the fastest path:
- Views live permanently in the database — no API, no service, no DTO, no frontend needed
- Query from the **Supabase dashboard → SQL Editor** with a single `SELECT * FROM v_audit_...`
- The summary rollup view gives instant health status in one query
- Views are queryable from any future tool (Metabase, API, scripts) without schema duplication
- Total dev overhead: one migration file, then run it once

**How to use after deployment:**
```sql
-- Health summary (run first)
SELECT * FROM v_audit_summary;

-- Drill into a specific scenario
SELECT * FROM v_audit_overpaid_enrollments;
SELECT * FROM v_audit_zero_charge_enrollments WHERE enrolled_at >= '2026-07-01';
```

---

## 3. Severity Tiers

| Tier | Meaning | Action |
|------|---------|--------|
| 🔴 **ERROR** | Direct financial risk — double charges, ghost money, unresolvable data | Investigate immediately, block affected reports |
| 🟡 **WARNING** | Financial discrepancy — likely needs correction but not immediately blocking | Review within same week |
| 🔵 **INFO** | Data hygiene — probably a migration artifact or benign state, but worth cleaning | Review and document |

### Scenario Assignments

| Scenario | Label | Tier | Rationale |
|----------|-------|------|-----------|
| A | Zero-Charge Active Enrollments | 🔵 INFO | May be intentional (scholarship), but unusual |
| B | Overpaid Enrollments | 🟡 WARNING | Credit owed — liability risk |
| C | Orphaned Payments (no enrollment link) | 🟡 WARNING | Money collected but unattributable |
| D | Duplicate Active Enrollments | 🔴 ERROR | Definite double-charge risk |
| E | Active Enrollments on Dead Groups | 🔵 INFO | Likely cleanup lag when a group ended |
| F | Dropped/Transferred with Unrefunded Balance | 🟡 WARNING | Money owed back to student |
| G | Level Mismatch (no group_levels row) | 🔵 INFO | Migration artifact — breaks analytics attribution |
| H | Active Payments for Soft-Deleted Students | 🔴 ERROR | Ghost money in revenue figures |
| I | Full/Over-Discounts (≥ 100% of amount_due) | 🟡 WARNING | Almost certainly a data entry error |

---

## 4. Anomaly Scenarios — Queries

All views support an optional `enrolled_after` / `paid_after` date to exclude pre-cutoff bulk-import artifacts. In the views themselves, filtering is done via a `WHERE` that can be added at query time.

---

### Scenario A 🔵 INFO — Zero-Charge Active Enrollments

```sql
-- View: v_audit_zero_charge_enrollments
SELECT
    e.id           AS enrollment_id,
    s.full_name    AS student_name,
    s.phone        AS student_phone,
    g.name         AS group_name,
    c.name         AS course_name,
    e.level_number,
    e.enrolled_at,
    e.amount_due,
    e.discount_applied,
    e.notes,
    e.created_at
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE e.status = 'active'
  AND (e.amount_due IS NULL OR e.amount_due = 0)
  AND s.deleted_at IS NULL
ORDER BY e.enrolled_at DESC;
```

---

### Scenario B 🟡 WARNING — Overpaid Enrollments (Credit Balances)

```sql
-- View: v_audit_overpaid_enrollments
SELECT
    e.id                                             AS enrollment_id,
    s.full_name                                      AS student_name,
    s.phone,
    g.name                                           AS group_name,
    c.name                                           AS course_name,
    e.level_number,
    e.amount_due,
    COALESCE(e.discount_applied, 0)                  AS discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, 0)) AS net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                     AS total_paid,
    (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
      - (e.amount_due - COALESCE(e.discount_applied, 0))
    )                                                AS overpaid_by
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE s.deleted_at IS NULL
GROUP BY e.id, s.full_name, s.phone, g.name, c.name,
         e.level_number, e.amount_due, e.discount_applied
HAVING (
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
  - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
) > (e.amount_due - COALESCE(e.discount_applied, 0))
ORDER BY overpaid_by DESC;
```

---

### Scenario C 🟡 WARNING — Orphaned Payments (No Enrollment Link)

```sql
-- View: v_audit_orphaned_payments
SELECT
    p.id               AS payment_id,
    r.receipt_number,
    s.full_name        AS student_name,
    s.phone,
    p.amount,
    p.transaction_type,
    p.payment_type,
    p.notes,
    r.paid_at,
    r.payment_method
FROM payments p
JOIN students s ON s.id = p.student_id
JOIN receipts r ON r.id = p.receipt_id
WHERE p.enrollment_id IS NULL
  AND p.payment_type = 'course_level'
  AND p.deleted_at IS NULL
  AND s.deleted_at IS NULL
ORDER BY r.paid_at DESC;
```

---

### Scenario D 🔴 ERROR — Duplicate Active Enrollments

```sql
-- View: v_audit_duplicate_enrollments
SELECT
    s.full_name        AS student_name,
    s.phone,
    g.name             AS group_name,
    c.name             AS course_name,
    COUNT(e.id)        AS active_enrollment_count,
    STRING_AGG(e.id::text, ', ' ORDER BY e.id) AS enrollment_ids,
    MIN(e.enrolled_at) AS first_enrolled,
    MAX(e.enrolled_at) AS last_enrolled
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE e.status = 'active'
  AND s.deleted_at IS NULL
GROUP BY s.id, s.full_name, s.phone, g.id, g.name, c.name
HAVING COUNT(e.id) > 1
ORDER BY active_enrollment_count DESC;
```

---

### Scenario E 🔵 INFO — Active Enrollments on Inactive/Archived Groups

```sql
-- View: v_audit_dead_group_enrollments
SELECT
    e.id           AS enrollment_id,
    s.full_name    AS student_name,
    s.phone,
    g.name         AS group_name,
    g.status       AS group_status,
    c.name         AS course_name,
    e.level_number,
    e.enrolled_at,
    e.amount_due,
    COALESCE(e.discount_applied, 0) AS discount_applied
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE e.status = 'active'
  AND g.status IN ('inactive','completed','archived')
  AND s.deleted_at IS NULL
ORDER BY g.status, g.name;
```

---

### Scenario F 🟡 WARNING — Dropped/Transferred with Unrefunded Balance

```sql
-- View: v_audit_unrefunded_exits
SELECT
    e.id                                             AS enrollment_id,
    s.full_name                                      AS student_name,
    s.phone,
    g.name                                           AS group_name,
    c.name                                           AS course_name,
    e.level_number,
    e.status                                         AS enrollment_status,
    e.amount_due,
    COALESCE(e.discount_applied, 0)                  AS discount_applied,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                     AS net_collected,
    e.transferred_from,
    e.notes
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE e.status IN ('dropped','transferred')
  AND s.deleted_at IS NULL
GROUP BY e.id, s.full_name, s.phone, g.name, c.name
HAVING (
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
  - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
) > 0
ORDER BY net_collected DESC;
```

---

### Scenario G 🔵 INFO — Level Mismatch (No group_levels Row)

Emit `data_quality_warning` in Report 4 (Round Cost) when this view has results — do not block the report.

```sql
-- View: v_audit_level_mismatch
SELECT
    e.id           AS enrollment_id,
    s.full_name    AS student_name,
    s.phone,
    g.name         AS group_name,
    c.name         AS course_name,
    e.level_number AS enrollment_level,
    e.status       AS enrollment_status,
    e.amount_due,
    e.enrolled_at
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE s.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM group_levels gl
      WHERE gl.group_id    = e.group_id
        AND gl.level_number = e.level_number
  )
ORDER BY e.enrolled_at DESC;
```

---

### Scenario H 🔴 ERROR — Active Payments for Soft-Deleted Students

```sql
-- View: v_audit_ghost_payments
SELECT
    p.id              AS payment_id,
    p.student_id,
    s.full_name       AS deleted_student_name,
    s.deleted_at      AS student_deleted_at,
    p.amount,
    p.transaction_type,
    p.enrollment_id,
    r.receipt_number,
    r.paid_at,
    p.created_at
FROM payments p
JOIN students s ON s.id = p.student_id
JOIN receipts r ON r.id = p.receipt_id
WHERE p.deleted_at IS NULL
  AND s.deleted_at IS NOT NULL
ORDER BY s.deleted_at DESC;
```

---

### Scenario I 🟡 WARNING — Full or Over-Discounts

```sql
-- View: v_audit_overdiscounted_enrollments
SELECT
    e.id                                                        AS enrollment_id,
    s.full_name                                                 AS student_name,
    s.phone,
    g.name                                                      AS group_name,
    c.name                                                      AS course_name,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    ROUND(e.discount_applied / NULLIF(e.amount_due, 0) * 100, 1) AS discount_pct,
    (e.amount_due - COALESCE(e.discount_applied, 0))            AS net_due,
    e.notes,
    e.enrolled_at,
    e.status
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE s.deleted_at IS NULL
  AND e.discount_applied IS NOT NULL
  AND e.discount_applied >= e.amount_due
ORDER BY discount_pct DESC NULLS LAST;
```

---

## 5. Summary Rollup View

```sql
-- View: v_audit_summary
-- Run this first. Any non-zero count tells you where to look next.
SELECT 'A' AS code, 'INFO'    AS severity, 'Zero-Charge Active Enrollments'            AS label,
       COUNT(*) AS anomaly_count
FROM enrollments e JOIN students s ON s.id = e.student_id
WHERE e.status = 'active' AND (e.amount_due IS NULL OR e.amount_due = 0) AND s.deleted_at IS NULL

UNION ALL

SELECT 'B', 'WARNING', 'Overpaid Enrollments (Credit Balances)', COUNT(*) FROM (
    SELECT e.id FROM enrollments e JOIN students s ON s.id = e.student_id
    LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
    WHERE s.deleted_at IS NULL
    GROUP BY e.id, e.amount_due, e.discount_applied
    HAVING (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
    ) > (e.amount_due - COALESCE(e.discount_applied, 0))
) sub

UNION ALL

SELECT 'C', 'WARNING', 'Orphaned Payments (No Enrollment Link)', COUNT(*) FROM payments p
JOIN students s ON s.id = p.student_id
WHERE p.enrollment_id IS NULL AND p.payment_type = 'course_level'
  AND p.deleted_at IS NULL AND s.deleted_at IS NULL

UNION ALL

SELECT 'D', 'ERROR', 'Duplicate Active Enrollments', COUNT(*) FROM (
    SELECT student_id, group_id FROM enrollments WHERE status = 'active'
    GROUP BY student_id, group_id HAVING COUNT(*) > 1
) sub

UNION ALL

SELECT 'E', 'INFO', 'Active Enrollments on Dead Groups', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id JOIN groups g ON g.id = e.group_id
WHERE e.status = 'active' AND g.status IN ('inactive','completed','archived') AND s.deleted_at IS NULL

UNION ALL

SELECT 'F', 'WARNING', 'Dropped/Transferred with Unrefunded Balance', COUNT(*) FROM (
    SELECT e.id FROM enrollments e JOIN students s ON s.id = e.student_id
    LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
    WHERE e.status IN ('dropped','transferred') AND s.deleted_at IS NULL
    GROUP BY e.id
    HAVING (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
    ) > 0
) sub

UNION ALL

SELECT 'G', 'INFO', 'Level Mismatch (no group_levels row)', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id
WHERE s.deleted_at IS NULL
  AND NOT EXISTS (SELECT 1 FROM group_levels gl
    WHERE gl.group_id = e.group_id AND gl.level_number = e.level_number)

UNION ALL

SELECT 'H', 'ERROR', 'Active Payments for Soft-Deleted Students', COUNT(*) FROM payments p
JOIN students s ON s.id = p.student_id
WHERE p.deleted_at IS NULL AND s.deleted_at IS NOT NULL

UNION ALL

SELECT 'I', 'WARNING', 'Full or Over-Discounts (≥ 100%)', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id
WHERE s.deleted_at IS NULL
  AND e.discount_applied IS NOT NULL AND e.discount_applied >= e.amount_due

ORDER BY code;
```

---

## 6. Deliverable: Migration `074_audit_views.sql`

Single migration file that creates all 10 views (`v_audit_summary` + 9 scenario views) as `CREATE OR REPLACE VIEW` — idempotent, safe to re-run.

**Location:** `db/migrations/074_audit_views.sql`

After applying the migration, use the Supabase dashboard SQL editor:
```sql
SELECT * FROM v_audit_summary;               -- health check
SELECT * FROM v_audit_duplicate_enrollments; -- ERROR tier drill-down
SELECT * FROM v_audit_overpaid_enrollments WHERE net_due > 0;
-- Add date filters to exclude migration artifacts:
SELECT * FROM v_audit_zero_charge_enrollments WHERE enrolled_at >= '2026-07-01';
```

No API, no service layer, no frontend development required for immediate visibility.

---

## 7. Future API Surface (deferred — not in this spec)

When/if a backend API is needed:
```
GET /analytics/audit/balance-integrity              → summary rollup
GET /analytics/audit/balance-integrity/{scenario}  → detail rows (a–i)
    Optional: ?enrolled_after=2026-07-01
```

Module: `app/modules/analytics/repositories/audit_repository.py` — queries reuse the same SQL as the views.

---

## 8. Investigation Workflow

```
1. SELECT * FROM v_audit_summary;
2. Note all non-zero rows — work ERRORs first, then WARNINGs, then INFO
3. For each non-zero scenario, run the detail view
4. Per anomaly row, classify:
   - Data entry error?         → flag for ops team correction
   - Migration artifact?       → document, add date-filter exclusion
   - Legitimate exception?     → document (scholarship, waiver) — whitelist
5. Open remediation issue if write action needed
   (write operations out of scope for this spec)
```

---

## 9. Out of Scope

- Write operations / data repair
- `team_members` competition balance audit
- Scheduled automated audit runs / push alerts (future)
- Frontend data health dashboard (future)
