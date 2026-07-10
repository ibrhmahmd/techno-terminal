# Research: Group Level Management

**Feature**: 037-group-level-management  
**Date**: 2026-07-10

---

## Finding 1: Cascading hard delete dependency graph

To hard delete a level cleanly and safely without hitting PostgreSQL constraint violations, we must handle foreign keys in the correct dependency order.

### Dependency Table

| Table | Dependency | Constraint Action | Required Cleanup Action |
|---|---|---|---|
| `enrollment_level_history` | FK `group_level_id` → `group_levels.id` | `ON DELETE RESTRICT` | **Delete first** |
| `sessions` | FK `group_level_id` → `group_levels.id` | `ON DELETE SET NULL` | Delete sessions first to prevent orphan session records |
| `attendance` | FK `session_id` → `sessions.id` | `ON DELETE RESTRICT` | **Guard blocks level delete** if any attendance exists on level sessions |
| `payments` | FK `enrollment_id` → `enrollments.id` | `ON DELETE SET NULL` | **Guard blocks level delete** if any payments exist on level enrollments |
| `group_course_history` | FK `group_id` → `groups.id` | `ON DELETE CASCADE` | Delete entries specifically matching the course change of this level progression |
| `student_activity_log` | No FK | N/A | Delete entries matching the `level_started` subtype for level progression |

### Validation Query Helpers
To check payments and attendance count, we will implement optimized queries in `repository.py`:
- `count_payments_for_level` counts payments joined via `enrollments` at the target level.
- `count_attendance_for_level` counts attendance records joined via `sessions` at the target level.

---

## Finding 2: Reverting Old Enrollment/Level Status on Undo

When a level progression is undone:
1. The **previous level** (e.g. Level N-1) must be set from `status = 'completed'` back to `status = 'active'` and its `effective_to` set back to `NULL`.
2. The **previous enrollments** that were marked `completed` during migration must be restored to `status = 'active'`. We must identify these by looking at all enrollments in the same group with `level_number = level_number - 1` and `status = 'completed'`.

---

## Finding 3: Synchronization of Group level_number pointer

`groups.level_number` is a denormalized field.
1. On **level deletion**, we must fetch the previous highest level number (typically `level_number - 1`) and update `groups.level_number`.
2. On **level cancellation**, we must do the same: if the cancelled level was the active/latest level, we rollback `groups.level_number` to the previous active level.

---

## Finding 4: Dead Code Elimination

Per §Dead Code Discipline of the Constitution:
- `GroupLevelCourseAssignment` has no DDL and no callers in the workspace. It is fully dead and must be deleted.
- `complete_current_level` route in `group_lifecycle_router.py` calls `svc.complete_current_level()` which does not exist in `GroupLevelService`. Progression is only managed via `progress_to_next_level` in `GroupLifecycleService`. This route is dead and will be deleted.
