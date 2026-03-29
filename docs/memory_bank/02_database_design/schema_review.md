# Schema Design Review — Consolidated (v3.1)

## Status: ✅ ALL ISSUES FROM BOTH REVIEWS RESOLVED

---

## First Review (12 Issues)

| # | Problem | Status | Resolution |
|---|---|---|---|
| P1 | `age` column drifts | ✅ Fixed | Dropped. Derived in `v_students` view. |
| P2 | `gender TEXT` no constraint | ✅ Fixed | `CHECK (gender IN ('male', 'female'))` |
| P3 | `sessions_attended` cached | ✅ Fixed | Removed. `v_enrollment_attendance` view. |
| P4 | `session_count` cached | ✅ Fixed | Removed. `v_group_session_count` view. |
| P5 | Discount in two places | ✅ Documented | enrollment = planned, payment = actual. |
| P6 | No `enrollment_id` on attendance | ✅ Fixed | Added FK. |
| P7 | `sibling_group_id` weak | ✅ Fixed | Replaced with `parents` table. |
| P8 | Phone/whatsapp on student | ✅ Fixed | Contact lives on `parents`. Student has optional phone for teens. |
| P9 | Role duplication | ✅ Fixed | `employees.job_title` (org) vs `users.role` (auth). |
| P10 | No CHECK on status columns | ✅ Fixed | CHECK constraints on all 11 status/enum columns. |
| P11 | No unique on active enrollments | ✅ Fixed | Partial unique index. |
| P12 | Contract payroll undefined | ✅ Documented | % of collected payments per group level. |

## Second Review (8 Issues)

| # | Problem | Status | Resolution |
|---|---|---|---|
| R1 | Sessions can't distinguish levels ("time travel") | ✅ Fixed | Added `sessions.level_number`. |
| R2 | Missing CHECK constraints (time, capacity, amount) | ✅ Fixed | 5 new CHECKs: time ranges, capacity > 0, amount > 0. |
| R3 | Split payments impossible | ✅ Fixed | Added `receipts` table. Payments are line items. |
| R4 | Students can't have phones | ✅ Fixed | Added `students.phone` (optional). |
| R5 | Parents need two numbers | ✅ Fixed | `phone_primary` + `phone_secondary`, removed `whatsapp`. |
| R6 | age stored (duplicate of R1-P1) | ✅ Already fixed | |
| R7 | FK indexing | ✅ Already fixed | 23 indexes. |
| R8 | Group name history on level change | ⚠️ Noted | UI concern. Admin must manually rename if desired. |

## Third Review (7 Issues - Production Safety)

| # | Problem | Status | Resolution |
|---|---|---|---|
| S1 | `sessions` ON DELETE CASCADE is a nuclear threat | ✅ Fixed | Changed to `ON DELETE RESTRICT`. |
| S2 | `payments` ON DELETE CASCADE destroys history | ✅ Fixed | Changed to `ON DELETE RESTRICT`. |
| S3 | `receipts.total_amount` allows mismatch drift | ✅ Fixed | Removed column. Receipt total is purely sum of line items. |
| S4 | Refunds impossible due to `amount > 0` | ✅ Fixed | Changed to `amount != 0` and added `transaction_type` (charge/payment/refund). |
| S5 | `attendance` orphans due to nullable `enrollment_id` | ✅ Fixed | Made `attendance.enrollment_id` NOT NULL. |
| S6 | Single parent constraint fails real-world split families | ✅ Fixed | Added `student_parents` junction table (many-to-many). |
| S7 | `users` vs `employees` role redundancy | ✅ Already fixed | (Addressed in v3.1 update, `employees` only has `job_title`). |

## Remaining V2/V3 Deferrals

| Item | Reason |
|---|---|
| Audit log table | V2 feature |
| Employee attendance | V2 with payroll |
| Multiple active enrollments logic | Deferring index change until business rules are finalized during web app development |
