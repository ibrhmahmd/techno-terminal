# Spec 037 — Group Level Management (Delete, Edit, Bug Fixes)

**Status:** DRAFT  
**Date:** 2026-07-10  
**Sprint Scope:** Backend only  
**Relates to:** `specs/034-payment-void-refund`, `specs/036-balance-integrity-audit`

---

## Decisions Log

| # | Question | Decision |
|---|----------|----------|
| 1 | Hard delete vs. soft delete for undo | **Hard delete** — remove the level row and all related records |
| 2 | Undo = full cascade or just delete level? | **Full cascade** — hard delete level + sessions + enrollments + history + rollback group state |
| 3 | Edit course_id on level → update group? | **No** — course change is level-only, group's `course_id` stays unchanged |
| 4 | Edit `sessions_planned`? | **No** — user manages sessions manually (add/delete individually) |
| 5 | Edit `instructor_id` → cascade to group/sessions? | **No** — only the level record is updated |
| 6 | Undo scope | Only the **latest** level can be undone (can't delete a middle level) |
| 7 | Blocking conditions | Block if level has **payments** or **attendance** records |

---

## 1. Problem Statement

Three problems exist in group level management:

1. **No undo for accidental level progression.** The client accidentally clicked "Progress Level" which migrated all enrollments to a new level. There is no way to reverse this. The existing `DELETE` endpoint has bugs that make it non-functional (DB constraint violation, overly strict guards).

2. **No level editing.** Once a level is created, its instructor and course cannot be changed. Admins must delete and recreate the level to fix mistakes.

3. **Multiple dead/broken endpoints.** Three endpoints crash at runtime due to method signature mismatches and missing implementations.

---

## 2. Scope

### In Scope
- **Feature A:** Undo/delete the latest level (hard delete with full cascade)
- **Feature B:** Edit level info (instructor, course, price, notes)
- **Bug fixes:** 5 confirmed bugs (see §5)

### Out of Scope
- Undoing a non-latest level (middle level deletion)
- Editing `sessions_planned` (user manages sessions individually)
- Cascade of level edits to group or sessions
- Frontend changes (backend API only this sprint)

---

## 3. Feature A — Undo Level (Hard Delete with Cascade)

### User Story

> As an admin, I accidentally progressed Group X to Level 3. All enrollments were migrated to the new level. I need to undo this so the group goes back to Level 2 with all students restored to their original enrollments.

### Preconditions & Guards

| Check | Behavior |
|---|---|
| Level doesn't exist | 404 NotFoundError |
| Level is not the latest (highest `level_number`) for the group | 409 BusinessRuleError — can only undo the most recent level |
| Level has **payments** (via enrollments at this level) | 409 ConflictError — "Level has N payments. Cancel instead." |
| Level has **attendance** records (via sessions at this level) | 409 ConflictError — "Level has N attendance records. Cancel instead." |
| Level is the only level (level_number = 1) | 409 BusinessRuleError — "Cannot delete the only level of a group" |
| All checks pass | Proceed with hard delete |

### Cascade Sequence (single transaction)

```
Phase 1: Validate
  └─ Verify level is latest, no payments, no attendance

Phase 2: Clean up enrollment migration
  ├─ Delete enrollment_level_history rows for this level
  ├─ Hard delete NEW enrollments at this level (created during migration)
  └─ Reactivate OLD enrollments at previous level (completed → active)

Phase 3: Clean up sessions
  └─ Hard delete ALL sessions linked to this group_level_id

Phase 4: Clean up history/logs
  ├─ Delete group_course_history entries created during this progression
  └─ Delete student_activity_log entries for "level_started" at this level

Phase 5: Delete the level
  └─ Hard delete the group_levels row

Phase 6: Rollback group state
  ├─ Set groups.level_number = previous level's number
  ├─ If previous level was completed by progression → set it back to 'active'
  └─ If course was changed during progression → revert groups.course_id

COMMIT
```

### Cross-Module Impact

| Module | Table | Impact | FK Behavior |
|---|---|---|---|
| **Academics** | `group_levels` | Row deleted | Target |
| **Academics** | `sessions` | Rows deleted (by group_level_id) | `ON DELETE SET NULL` — but we hard delete explicitly |
| **Enrollments** | `enrollments` | New rows deleted, old rows reactivated | No FK to group_levels — matched by `(group_id, level_number)` |
| **Enrollments** | `enrollment_level_history` | Rows deleted | `ON DELETE RESTRICT` on group_level_id — must delete before level |
| **Enrollments** | `attendance` | **Guard blocks delete if any exist** | `ON DELETE RESTRICT` on session_id |
| **Finance** | `payments` | **Guard blocks delete if any exist** | `ON DELETE SET NULL` on enrollment_id |
| **CRM** | `student_activity_log` | Rows deleted (level_started entries) | No FK constraint |
| **Academics** | `group_course_history` | Rows deleted if course changed | `ON DELETE CASCADE` on group_id |
| **Academics** | `groups` | `level_number` rolled back, possibly `course_id` reverted | Parent record updated |

### API Endpoint

```
DELETE /academics/groups/{group_id}/levels/{level_number}
Auth: require_admin
```

**Response (success):**
```json
{
  "success": true,
  "data": {
    "level_number_deleted": 3,
    "reverted_to_level": 2,
    "sessions_deleted": 5,
    "enrollments_deleted": 12,
    "enrollments_reactivated": 12,
    "group_level_number_after": 2
  },
  "message": "Level 3 deleted. Group reverted to Level 2. 12 enrollments restored."
}
```

**Response (blocked):**
```json
{
  "success": false,
  "error": "ConflictError",
  "message": "Cannot delete level 3: it has 5 payments and 12 attendance records. Use cancel level instead."
}
```

### DTOs

```python
# lifecycle/schemas.py

class DeleteLevelResult(BaseModel):
    """Result of undoing/deleting a level."""
    level_number_deleted: int
    reverted_to_level: int
    sessions_deleted: int
    enrollments_deleted: int
    enrollments_reactivated: int
    group_level_number_after: int

class DeleteLevelBlockedDTO(BaseModel):
    """Details when delete is blocked."""
    payments_count: int
    attendance_count: int
    enrollments_count: int
```

---

## 4. Feature B — Edit Level Info

### User Story

> As an admin, I need to change the instructor or course assigned to a specific level without deleting and recreating it.

### Editable Fields

| Field | Allowed | Cascade |
|---|---|---|
| `instructor_id` | ✅ | Level record only |
| `course_id` | ✅ | Level record only (group unchanged) |
| `price_override` | ✅ | Level record only (existing enrollments unchanged) |
| `notes` | ✅ | Level record only |
| `sessions_planned` | ❌ | Not editable — user manages sessions manually |
| `status` | ❌ | Use progress/cancel/complete endpoints |
| `level_number` | ❌ | Immutable |

### Preconditions

| Check | Behavior |
|---|---|
| Level doesn't exist | 404 NotFoundError |
| Level status is `completed` or `cancelled` | 409 BusinessRuleError — can only edit active levels |
| `instructor_id` provided but doesn't exist | 404 NotFoundError |
| `course_id` provided but doesn't exist | 404 NotFoundError |

### API Endpoint

```
PATCH /academics/groups/{group_id}/levels/{level_number}
Auth: require_admin
```

**Request body:**
```json
{
  "instructor_id": 5,
  "course_id": 3,
  "price_override": 350.00,
  "notes": "Changed instructor mid-round"
}
```

All fields optional — partial update.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "group_id": 10,
    "level_number": 2,
    "course_id": 3,
    "course_name": "EV3",
    "instructor_id": 5,
    "instructor_name": "Mariam Tawfik",
    "sessions_planned": 5,
    "price_override": 350.00,
    "status": "active",
    "effective_from": "2026-07-01T00:00:00Z",
    "effective_to": null,
    "created_at": "2026-07-01T00:00:00Z"
  },
  "message": "Level 2 updated successfully."
}
```

### DTOs

```python
# level/schemas.py

class UpdateLevelInput(BaseModel):
    """Partial update input for a group level."""
    instructor_id: Optional[int] = None
    course_id: Optional[int] = None
    price_override: Optional[Decimal] = None
    notes: Optional[str] = None
```

---

## 5. Bug Fixes

### Bug 1: `soft_delete_level` — invalid status value
**Location:** [level/repository.py:177-195](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/level/repository.py#L177-L195)  
**Problem:** Sets `status = "deleted"` — DB CHECK constraint only allows `{active, completed, cancelled}`.  
**Fix:** Remove `soft_delete_level` entirely. Replace with Feature A's hard delete. The function is dead after Feature A lands.

### Bug 2: `cancel_level_endpoint` — arg count mismatch
**Location:** [group_lifecycle_router.py:118](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/academics/group_lifecycle_router.py#L118)  
**Problem:** Router calls `svc.cancel_level(group_id, level_number, body.reason)` — 3 args. Service method accepts 2.  
**Fix:** Add `reason: Optional[str] = None` parameter to `GroupLevelService.cancel_level()`. Store reason in `level.notes` if not None.

### Bug 3: `complete_group_level` endpoint — calls nonexistent method
**Location:** [group_lifecycle_router.py:76](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/academics/group_lifecycle_router.py#L76)  
**Problem:** Calls `svc.complete_current_level(group_id)` — method doesn't exist on `GroupLevelService`.  
**Fix:** Remove this dead endpoint entirely. Level completion is handled by `progress_to_next_level` in the lifecycle service.

### Bug 4: `GroupLevelCourseAssignment` — dead model
**Location:** [group_level_models.py:68-81](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/models/group_level_models.py#L68-L81)  
**Problem:** ORM model maps to `group_level_course_assignments` table — no DDL exists, no callers.  
**Fix:** Delete the model class. Per Dead Code Discipline in constitution.

### Bug 5: `groups.level_number` — not synced on cancel
**Location:** [level/service.py:124-132](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/level/service.py#L124-L132)  
**Problem:** Cancelling the latest level doesn't rollback `groups.level_number`.  
**Fix:** After cancel, check if the cancelled level was the current `groups.level_number`. If so, find the previous active level and update `groups.level_number` to match.

---

## 6. Architecture Compliance

### Constitution Validation

| Principle | Compliance |
|---|---|
| §I Router→Service→Repository | ✅ Delete orchestration in lifecycle service, not router |
| §II D+ Hybrid slices | ✅ Delete goes in `lifecycle/` (orchestrator). Edit goes in `level/` (single-entity ops) |
| §III Typed Contracts | ✅ All returns are named DTOs — `DeleteLevelResult`, `GroupLevelDetailDTO` |
| §IV Response Envelope | ✅ Standard `ApiResponse` wrapper |
| §IV Domain Exceptions | ✅ `NotFoundError`, `ConflictError`, `BusinessRuleError` — no raw `ValueError` or `HTTPException` in services |
| §V Auth Guards | ✅ Both endpoints: `require_admin` |
| Dead Code Discipline | ✅ Removing `soft_delete_level`, `GroupLevelCourseAssignment`, dead `complete` endpoint |

### Service Placement

| Operation | Slice | Reason |
|---|---|---|
| Delete level (cascade undo) | `lifecycle/service.py` | Multi-entity orchestration across modules |
| Edit level | `level/service.py` | Single-entity mutation, no cross-module cascade |
| Bug fixes (cancel sync) | `level/service.py` | Single-entity concern |

---

## 7. Files Changed

### Modified Files

| File | Changes |
|---|---|
| `app/modules/academics/group/lifecycle/service.py` | Add `delete_level()` orchestrator method |
| `app/modules/academics/group/lifecycle/schemas.py` | Add `DeleteLevelResult` DTO |
| `app/modules/academics/group/lifecycle/interface.py` | Add `delete_level` to protocol |
| `app/modules/academics/group/level/service.py` | Add `update_level()`, fix `cancel_level()` signature, add level_number rollback |
| `app/modules/academics/group/level/schemas.py` | Add `UpdateLevelInput` DTO |
| `app/modules/academics/group/level/interface.py` | Add `update_level` to protocol |
| `app/modules/academics/group/level/repository.py` | Remove `soft_delete_level`, add guard queries (payments count, attendance count) |
| `app/modules/academics/group/details/service.py` | Remove `delete_level()` — moved to lifecycle |
| `app/modules/academics/group/details/interface.py` | Remove `delete_level` from protocol |
| `app/api/routers/academics/group_details_router.py` | Update DELETE endpoint to use lifecycle service |
| `app/api/routers/academics/group_lifecycle_router.py` | Remove dead `complete` endpoint, fix `cancel` arg mismatch, add PATCH level |
| `app/modules/academics/models/group_level_models.py` | Delete `GroupLevelCourseAssignment` class |
| `app/modules/academics/__init__.py` | Update exports |

### New Files
None — all changes fit in existing files.

### Migration
| File | Purpose |
|---|---|
| `db/migrations/084_no_schema_change.sql` | No DDL changes needed — all operations are DML (INSERT/UPDATE/DELETE on existing tables) |

---

## 8. Test Plan

### New Test Cases

```python
# tests/test_group_levels.py

# Feature A — Delete Level
test_delete_latest_level_clean()              # No enrollments, no sessions → clean delete
test_delete_level_with_migrated_enrollments()  # Enrollments migrated → cascade undo
test_delete_level_blocked_by_payments()        # Has payments → 409
test_delete_level_blocked_by_attendance()      # Has attendance → 409
test_delete_level_not_latest_blocked()         # Trying to delete middle level → 409
test_delete_only_level_blocked()               # Level 1 is the only level → 409
test_delete_level_rollback_group_state()       # Verify groups.level_number reverts
test_delete_level_reactivates_old_enrollments()# Old enrollments status → active

# Feature B — Edit Level
test_edit_level_instructor()                   # Change instructor → level only
test_edit_level_course()                       # Change course → level only, group unchanged
test_edit_level_price_override()               # Change price → level only
test_edit_completed_level_blocked()            # Completed level → 409
test_edit_cancelled_level_blocked()            # Cancelled level → 409
test_edit_level_nonexistent_instructor()       # Bad instructor_id → 404
test_edit_level_nonexistent_course()            # Bad course_id → 404

# Bug Fixes
test_cancel_level_with_reason()                # Reason stored in notes
test_cancel_level_rolls_back_group_number()    # groups.level_number synced
```

### Existing Tests — Regression Check
```bash
pytest tests/test_academics.py -v
pytest tests/test_crm.py -v
pytest tests/test_finance.py -v
```
