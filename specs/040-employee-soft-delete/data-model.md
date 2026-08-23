# Data Model: Employee Soft Delete

**Feature**: 040-employee-soft-delete | **Date**: 2026-08-24

## Entity: Employee (modified)

Existing HR aggregate root. Gains two nullable columns; nothing else changes.

| Field | Type | Constraint | Notes |
|-------|------|------------|-------|
| `deleted_at` | `TIMESTAMPTZ`, nullable | — | Set by delete, cleared by restore. Non-null ⇒ row invisible to default reads |
| `deleted_by` | `INTEGER`, nullable | `REFERENCES users(id)` | Acting admin's local user id; always non-null when `deleted_at` is set |

**Uniqueness changes**:

| Identifier | Before | After |
|------------|--------|-------|
| `email` | `UNIQUE` table constraint | Partial unique index `uq_employees_email` … `WHERE deleted_at IS NULL` |
| `national_id` | `UNIQUE` table constraint | Partial unique index `uq_employees_national_id` … `WHERE deleted_at IS NULL` |
| `phone` | `UNIQUE` table constraint | Partial unique index `uq_employees_phone` … `WHERE deleted_at IS NULL` |
| `user_id` | `UNIQUE` table constraint | **Unchanged** — one login ↔ one employee ever (spec FR-008) |

Index names are preserved exactly so `app/modules/hr/services/integrity_error_mapper.py` continues translating constraint violations without modification.

## Entity: User / Staff Account (lifecycle edge only)

No schema change. New transition edge: **active → blocked when its employee is deleted** (same transaction). The `users.employee_id` ↔ `employees.user_id` link pair is deliberately preserved through deletion and restore so audit context survives.

## Relationships touched by soft delete (all preserved, none cascaded)

| Referencing table | FK behavior on HARD delete | Effect of SOFT delete |
|---|---|---|
| `users.employee_id` | SET NULL | None — link kept |
| `groups.instructor_id` | SET NULL | None — history intact |
| `group_levels.instructor_id` | SET NULL | None — history intact |
| `sessions.actual_instructor_id` | SET NULL | None — history intact |
| `teams.coach_id` | SET NULL | None — history intact |
| `tasks.assigned_to` | SET NULL | None — history intact |
| task time-logs `.employee_id` | CASCADE | None — rows untouched |

Soft delete never fires any ON DELETE rule; referencing rows are byte-identical before and after.

## State Transitions

```text
                    PUT {is_active:false}            DELETE /{id}
  [live active] ───────────────────────► [live inactive] ────┐
        │                                      ▲             │ deleted_at=now(), deleted_by=admin
        │ PUT {is_active:true}                 │             │ (+ user.is_active=false if linked)
        └──────────────────────────────────────┘             ▼
                                                    [deleted]
        POST /{id}/restore ◄──────────────────────────────── ┤
        deleted_at=NULL, deleted_by=NULL                      │ (restore rejected 409
        account stays blocked                                 │  if identity collides
                                                              │  with any live employee)
```

Invariants:
1. `deleted_at IS NULL ⟺ deleted_by IS NULL` (set/cleared together).
2. At most one LIVE employee per (email | national_id | phone) — enforced by partial indexes AND service probes.
3. At most one employee per `user_id`, live or deleted.
4. A deleted employee never appears in default reads or the staff-accounts overview.
5. Restore requires zero identity collision with the live set.

## Validation rules introduced

- Delete target must exist and be live → else `NotFoundError` (uniform double-delete outcome).
- Restore target must exist (`NotFoundError`) and be deleted (`ConflictError`, state-named).
- Restore collision probe aggregates ALL colliding fields into one `ConflictError` message (039 F-01 pattern), excluding the restored row itself.
