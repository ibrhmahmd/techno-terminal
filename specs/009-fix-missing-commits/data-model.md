# Data Model: Missing Commit Fix

**Phase**: Phase 1 — Design  
**Note**: No new entities or schema changes. This documents the existing entity state transitions affected by the fix.

---

## Enrollment

### State Transitions

```
Enrolled (active) ──► Transferred (old enrollment)
                  ──► Dropped
                  ──► Completed
```

| Transition | Method | Target Status | Notes |
|------------|--------|---------------|-------|
| Create | `enroll_student` | `active` | Also activates `waiting` students |
| Transfer | `transfer_student` | `transferred` (old), `active` (new) | Creates new enrollment row |
| Drop | `drop_enrollment` | `dropped` | Soft removal |
| Complete | `complete_enrollment` | `completed` | Level finished |
| Discount | `apply_sibling_discount` | (no status change) | Updates `discount_applied` |

---

## Competition

### State Transitions

```
Draft ──► Active (after creation)
Active ──► Deleted (soft delete, sets deleted_at)
```

## Team

### State Transitions

```
Creating ──► Active (after register_team)
Active ──► Placed (after update_placement sets placement_rank)
Active ──► Deleted (soft delete, sets deleted_at)
Deleted ──► Active (restore, clears deleted_at)
```

## GroupCompetitionParticipation

Created alongside team registration. Placement synced when team placement is set.
